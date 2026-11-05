'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const path = require('node:path');
const { DEFAULT_STATE_DIRECTORY } = require('./idempotency.cjs');
const { validateSupplier } = require('../contracts/index.cjs');

async function createImmutableFile(filePath, contents) {
  const directory = path.dirname(filePath);
  await fs.mkdir(directory, { recursive: true });
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
    await fs.link(tempPath, filePath);
    created = true;
    let directoryHandle;
    try {
      directoryHandle = await fs.open(directory, 'r');
      await directoryHandle.sync();
    } catch (error) {
      if (!['EACCES', 'EBADF', 'EISDIR', 'EINVAL', 'EPERM', 'ENOTSUP', 'EOPNOTSUPP'].includes(error && error.code)) throw error;
    } finally {
      if (directoryHandle) await directoryHandle.close().catch(() => {});
    }
  } catch (error) {
    if (!error || error.code !== 'EEXIST') throw error;
  } finally {
    await fs.unlink(tempPath).catch(() => {});
  }
  return created;
}

/**
 * Persist real supplier names only in the explicitly internal name log.
 * Keep this directory outside the repository and never use its contents for
 * screen output. Files are keyed by hashes, not by company identifiers.
 */
async function recordInternalSupplierName(supplier, { directory = path.join(DEFAULT_STATE_DIRECTORY, 'internal-name-log') } = {}) {
  const validation = validateSupplier(supplier);
  if (!validation.valid) throw new TypeError(`Invalid supplier cannot be added to the internal name log: ${validation.errors.join('; ')}`);
  const label = supplier.display_label;
  const name = supplier.name_internal;
  const identityHash = crypto.createHash('sha256')
    .update(JSON.stringify([label, name]))
    .digest('hex');
  const filePath = path.join(path.resolve(directory), `${identityHash}.json`);
  const body = JSON.stringify({
    visibility: 'INTERNAL_ONLY',
    display_label: label,
    name_internal: name,
  });
  const created = await createImmutableFile(filePath, body);
  if (!created) {
    const existing = JSON.parse(await fs.readFile(filePath, 'utf8'));
    if (existing.visibility !== 'INTERNAL_ONLY' || existing.display_label !== label || existing.name_internal !== name) {
      throw new Error('Internal name log record could not be verified');
    }
  }
  return { status: created ? 'CREATED' : 'EXISTS', display_label: label };
}

module.exports = Object.freeze({ recordInternalSupplierName });
