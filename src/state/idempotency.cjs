'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

const VERSION = 1;
const DEFAULT_STATE_DIRECTORY = path.join(os.homedir(), '.contextcon-supplier-agent', 'state');

/*
 * This journal publishes simulated local filesystem records only. It does not
 * guarantee exactly-once delivery to an external provider API; those
 * writes need provider idempotency or their own reconciliation path. On
 * Windows, file contents are flushed before publication, but directory fsync
 * is unavailable, so sudden power loss may lose directory-entry updates.
 */

function isPlainRecord(value) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function canonicalize(value, seen = new Set()) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new TypeError('Idempotency data cannot contain non-finite numbers');
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    if (seen.has(value)) throw new TypeError('Idempotency data cannot contain cycles');
    seen.add(value);
    const result = `[${value.map((entry) => canonicalize(entry, seen)).join(',')}]`;
    seen.delete(value);
    return result;
  }
  if (isPlainRecord(value)) {
    if (seen.has(value)) throw new TypeError('Idempotency data cannot contain cycles');
    seen.add(value);
    const fields = Object.keys(value).sort().map((key) => {
      if (value[key] === undefined) throw new TypeError('Idempotency data cannot contain undefined values');
      return `${JSON.stringify(key)}:${canonicalize(value[key], seen)}`;
    });
    seen.delete(value);
    return `{${fields.join(',')}}`;
  }
  throw new TypeError('Idempotency data must contain only JSON-compatible values');
}

function digest(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function isProcessAlive(pid) {
  if (!Number.isInteger(pid) || pid < 1) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (error && error.code === 'EPERM') return true;
    if (error && error.code === 'ESRCH') return false;
    // Unknown process-status errors are treated as live so we never take over
    // a reservation that might still be performing its write.
    return true;
  }
}

async function syncDirectory(directory) {
  let handle;
  try {
    handle = await fs.open(directory, 'r');
    await handle.sync();
  } catch (error) {
    // Windows does not allow directory handles to be flushed this way. The
    // contents are still fsynced before the atomic link; tolerate only the
    // known unsupported-directory cases.
    if (!['EACCES', 'EBADF', 'EISDIR', 'EINVAL', 'EPERM', 'ENOTSUP', 'EOPNOTSUPP'].includes(error && error.code)) {
      throw error;
    }
  } finally {
    if (handle) await handle.close().catch(() => {});
  }
}

async function createImmutableFile(filePath, contents) {
  const directory = path.dirname(filePath);
  const tempPath = path.join(directory, `.${path.basename(filePath)}.${process.pid}.${crypto.randomBytes(8).toString('hex')}.tmp`);
  const handle = await fs.open(tempPath, 'wx', 0o600);
  try {
    await handle.writeFile(contents, 'utf8');
    await handle.sync();
  } finally {
    await handle.close();
  }

  let created = false;
  try {
    // Hard-linking a flushed temporary file publishes it atomically without
    // replacing a record another process has already created.
    await fs.link(tempPath, filePath);
    created = true;
    await syncDirectory(directory);
  } catch (error) {
    if (!error || error.code !== 'EEXIST') throw error;
  } finally {
    await fs.unlink(tempPath).catch(() => {});
  }
  return created;
}

async function readJson(filePath) {
  try {
    return { exists: true, value: JSON.parse(await fs.readFile(filePath, 'utf8')) };
  } catch (error) {
    if (error && error.code === 'ENOENT') return { exists: false, value: null };
    return { exists: true, value: null };
  }
}

class IdempotencyStore {
  constructor({ directory = DEFAULT_STATE_DIRECTORY } = {}) {
    if (typeof directory !== 'string' || directory.trim() === '') {
      throw new TypeError('Idempotency store directory must be a non-empty path');
    }
    this.directory = path.resolve(directory);
  }

  async _ready() {
    await fs.mkdir(this.directory, { recursive: true });
  }

  _paths(key) {
    const id = digest(key);
    return {
      intent: path.join(this.directory, `${id}.intent.json`),
      effect: path.join(this.directory, `${id}.effect.json`),
      complete: path.join(this.directory, `${id}.complete.json`),
      uncertain: path.join(this.directory, `${id}.uncertain.json`),
    };
  }

  async _readEffect(paths, key, payloadHash) {
    const file = await readJson(paths.effect);
    if (!file.exists) return { status: 'ABSENT' };
    const value = file.value;
    let resultHash;
    try {
      resultHash = digest(canonicalize(value && value.result));
    } catch {
      return { status: 'UNTRUSTWORTHY' };
    }
    if (!value || value.version !== VERSION || value.key !== key || value.payload_hash !== payloadHash
      || typeof value.result_hash !== 'string' || value.result_hash !== resultHash) {
      return { status: 'UNTRUSTWORTHY' };
    }
    return { status: 'FOUND', result: value.result };
  }

  async _readTerminal(filePath, key, payloadHash, expectedState) {
    const file = await readJson(filePath);
    if (!file.exists) return { status: 'ABSENT' };
    const value = file.value;
    if (!value || value.version !== VERSION || value.key !== key || value.payload_hash !== payloadHash || value.state !== expectedState) {
      return { status: 'UNTRUSTWORTHY' };
    }
    if (expectedState === 'COMPLETE') {
      try {
        if (typeof value.result_hash !== 'string' || value.result_hash !== digest(canonicalize(value.result))) {
          return { status: 'UNTRUSTWORTHY' };
        }
      } catch {
        return { status: 'UNTRUSTWORTHY' };
      }
    }
    return { status: 'FOUND', value };
  }

  async _markUncertain(paths, key, payloadHash, reason) {
    const body = JSON.stringify({ version: VERSION, key, payload_hash: payloadHash, state: 'IN_DOUBT', reason });
    try {
      await createImmutableFile(paths.uncertain, body);
    } catch {
      // The caller still receives IN_DOUBT. Leaving the intent without a
      // terminal record is safe: a future retry will reconcile and fail closed.
    }
    return { status: 'IN_DOUBT' };
  }

  async _finish(paths, key, payloadHash, result, status) {
    const resultJson = canonicalize(result);
    const body = JSON.stringify({
      version: VERSION,
      key,
      payload_hash: payloadHash,
      state: 'COMPLETE',
      result: JSON.parse(resultJson),
      result_hash: digest(resultJson),
    });
    try {
      const created = await createImmutableFile(paths.complete, body);
      const terminal = await this._readTerminal(paths.complete, key, payloadHash, 'COMPLETE');
      if (terminal.status !== 'FOUND') return { status: 'IN_DOUBT' };
      if (terminal.value.result_hash !== digest(resultJson)) return { status: 'IN_DOUBT' };
      return { status: created ? status : 'EXISTS', result: terminal.value.result };
    } catch {
      // The durable effect is still discoverable and can be reconciled on the
      // next call. Do not overwrite it or invoke the writer again.
      return { status: 'IN_DOUBT' };
    }
  }

  async executeOnce({ idempotencyKey, payload, write }) {
    if (typeof idempotencyKey !== 'string' || idempotencyKey.trim() === '') {
      throw new TypeError('idempotencyKey must be a non-empty string');
    }
    if (typeof write !== 'function') throw new TypeError('write must be a function');

    const key = idempotencyKey;
    const payloadJson = canonicalize(payload);
    const payloadHash = digest(payloadJson);
    await this._ready();
    const paths = this._paths(key);
    const intentBody = JSON.stringify({
      version: VERSION,
      key,
      payload_hash: payloadHash,
      owner_pid: process.pid,
      created_at: new Date().toISOString(),
    });

    const reservedHere = await createImmutableFile(paths.intent, intentBody);
    const intent = await readJson(paths.intent);
    if (!intent.exists || !intent.value || intent.value.version !== VERSION || intent.value.key !== key
      || typeof intent.value.payload_hash !== 'string' || !Number.isInteger(intent.value.owner_pid)) {
      return { status: 'IN_DOUBT' };
    }
    if (intent.value.payload_hash !== payloadHash) return { status: 'KEY_CONFLICT' };

    const complete = await this._readTerminal(paths.complete, key, payloadHash, 'COMPLETE');
    if (complete.status === 'FOUND') return { status: 'EXISTS', result: complete.value.result };
    if (complete.status === 'UNTRUSTWORTHY') return { status: 'IN_DOUBT' };
    const uncertain = await this._readTerminal(paths.uncertain, key, payloadHash, 'IN_DOUBT');
    if (uncertain.status === 'FOUND' || uncertain.status === 'UNTRUSTWORTHY') return { status: 'IN_DOUBT' };

    if (!reservedHere) {
      if (isProcessAlive(intent.value.owner_pid)) return { status: 'IN_PROGRESS' };
      const recovered = await this._readEffect(paths, key, payloadHash).catch(() => ({ status: 'UNTRUSTWORTHY' }));
      if (recovered.status === 'FOUND') return this._finish(paths, key, payloadHash, recovered.result, 'RECOVERED');
      return this._markUncertain(paths, key, payloadHash, recovered.status.toLowerCase());
    }

    let persistCalls = 0;
    const persistResult = async (result) => {
      persistCalls += 1;
      if (persistCalls !== 1) throw new Error('persistResult may be called only once per write attempt');
      const currentIntent = await readJson(paths.intent);
      if (!currentIntent.value || currentIntent.value.owner_pid !== process.pid
        || currentIntent.value.payload_hash !== payloadHash || currentIntent.value.key !== key) {
        throw new Error('This process does not own the durable idempotency reservation');
      }
      const done = await this._readTerminal(paths.complete, key, payloadHash, 'COMPLETE');
      const doubt = await this._readTerminal(paths.uncertain, key, payloadHash, 'IN_DOUBT');
      if (done.status !== 'ABSENT' || doubt.status !== 'ABSENT') throw new Error('The action is already terminal');

      const resultJson = canonicalize(result);
      const envelope = JSON.stringify({
        version: VERSION,
        key,
        payload_hash: payloadHash,
        result: JSON.parse(resultJson),
        result_hash: digest(resultJson),
      });
      const created = await createImmutableFile(paths.effect, envelope);
      const effect = await this._readEffect(paths, key, payloadHash);
      if (effect.status !== 'FOUND' || canonicalize(effect.result) !== resultJson) {
        throw new Error('A different or untrustworthy effect record already exists for this key');
      }
      return created ? 'CREATED' : 'EXISTS';
    };

    try {
      const returned = await write({ persistResult });
      if (persistCalls !== 1) return this._markUncertain(paths, key, payloadHash, 'write-returned-without-persisted-result');
      const effect = await this._readEffect(paths, key, payloadHash);
      if (effect.status !== 'FOUND' || canonicalize(effect.result) !== canonicalize(returned)) {
        return this._markUncertain(paths, key, payloadHash, 'write-result-did-not-match-durable-effect');
      }
      return this._finish(paths, key, payloadHash, effect.result, 'CREATED');
    } catch {
      const effect = await this._readEffect(paths, key, payloadHash).catch(() => ({ status: 'UNTRUSTWORTHY' }));
      if (effect.status === 'FOUND') return this._finish(paths, key, payloadHash, effect.result, 'RECOVERED');
      return this._markUncertain(paths, key, payloadHash, effect.status.toLowerCase());
    }
  }
}

function createIdempotencyStore(options) {
  return new IdempotencyStore(options);
}

module.exports = Object.freeze({
  DEFAULT_STATE_DIRECTORY,
  IdempotencyStore,
  createIdempotencyStore,
});
