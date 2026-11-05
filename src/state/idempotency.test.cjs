'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const test = require('node:test');
const { createIdempotencyStore } = require('./idempotency.cjs');

async function makeDirectory() {
  return fs.mkdtemp(path.join(os.tmpdir(), 'contextcon-idempotency-'));
}

async function removeDirectory(directory) {
  await fs.rm(directory, { recursive: true, force: true });
}

function runChild(source, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ['-e', source, ...args], { stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '';
    let stderr = '';
    child.stdout.setEncoding('utf8').on('data', (chunk) => { stdout += chunk; });
    child.stderr.setEncoding('utf8').on('data', (chunk) => { stderr += chunk; });
    child.once('error', reject);
    child.once('close', (code, signal) => resolve({ code, signal, stdout, stderr }));
  });
}

async function waitForFile(filePath, timeoutMs = 5000) {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    try {
      await fs.access(filePath);
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }
  throw new Error('Timed out waiting for the test reservation');
}

function keyFile(directory, key, suffix) {
  const id = crypto.createHash('sha256').update(key).digest('hex');
  return path.join(directory, `${id}.${suffix}.json`);
}

test('same-key retries after success return the immutable result without a second write', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const store = createIdempotencyStore({ directory });
  let writes = 0;
  const args = {
    idempotencyKey: 'po:v1:sample',
    payload: { total_cents: 8400, display_label: 'Supplier 1' },
    write: async ({ persistResult }) => {
      writes += 1;
      const result = { idempotency_key: 'po:v1:sample', display_label: 'Supplier 1', label: 'SIMULATED' };
      await persistResult(result);
      return result;
    },
  };

  const first = await store.executeOnce(args);
  const retry = await store.executeOnce(args);
  assert.equal(first.status, 'CREATED');
  assert.equal(retry.status, 'EXISTS');
  assert.deepEqual(retry.result, first.result);
  assert.equal(writes, 1);
});

test('same key with a different payload fails before invoking the writer', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const store = createIdempotencyStore({ directory });
  const first = await store.executeOnce({
    idempotencyKey: 'vendor:v1:sample',
    payload: { display_label: 'Supplier 1', total_cents: 8400 },
    write: async ({ persistResult }) => {
      const result = { label: 'SIMULATED', display_label: 'Supplier 1' };
      await persistResult(result);
      return result;
    },
  });
  let secondWriteCalled = false;
  const collision = await store.executeOnce({
    idempotencyKey: 'vendor:v1:sample',
    payload: { display_label: 'Supplier 2', total_cents: 8400 },
    write: async () => { secondWriteCalled = true; },
  });
  assert.equal(first.status, 'CREATED');
  assert.equal(collision.status, 'KEY_CONFLICT');
  assert.equal(secondWriteCalled, false);
});

test('crash after durable intent but before output fails closed on retry', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const modulePath = path.resolve(__dirname, 'idempotency.cjs');
  const crash = await runChild(`
    const { createIdempotencyStore } = require(process.argv[1]);
    const store = createIdempotencyStore({ directory: process.argv[2] });
    store.executeOnce({
      idempotencyKey: 'po:crash-before-output',
      payload: { display_label: 'Supplier 1', total_cents: 8400 },
      write: async () => { process.exit(71); },
    }).catch(() => process.exit(72));
  `, [modulePath, directory]);
  assert.equal(crash.code, 71, crash.stderr);

  let retryWriterCalled = false;
  const retry = await createIdempotencyStore({ directory }).executeOnce({
    idempotencyKey: 'po:crash-before-output',
    payload: { display_label: 'Supplier 1', total_cents: 8400 },
    write: async () => { retryWriterCalled = true; },
  });
  assert.equal(retry.status, 'IN_DOUBT');
  assert.equal(retryWriterCalled, false);
  assert.equal((await fs.readdir(directory)).filter((name) => name.endsWith('.effect.json')).length, 0);
});

test('crash after output but before terminal status recovers the same record without rewriting', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const modulePath = path.resolve(__dirname, 'idempotency.cjs');
  const crash = await runChild(`
    const { createIdempotencyStore } = require(process.argv[1]);
    const store = createIdempotencyStore({ directory: process.argv[2] });
    const result = { idempotency_key: 'po:crash-after-output', display_label: 'Supplier 1', label: 'SIMULATED' };
    store.executeOnce({
      idempotencyKey: 'po:crash-after-output',
      payload: { display_label: 'Supplier 1', total_cents: 8400 },
      write: async ({ persistResult }) => { await persistResult(result); process.exit(72); },
    }).catch(() => process.exit(73));
  `, [modulePath, directory]);
  assert.equal(crash.code, 72, crash.stderr);

  let retryWriterCalled = false;
  const retry = await createIdempotencyStore({ directory }).executeOnce({
    idempotencyKey: 'po:crash-after-output',
    payload: { display_label: 'Supplier 1', total_cents: 8400 },
    write: async () => { retryWriterCalled = true; },
  });
  assert.equal(retry.status, 'RECOVERED');
  assert.deepEqual(retry.result, {
    idempotency_key: 'po:crash-after-output', display_label: 'Supplier 1', label: 'SIMULATED',
  });
  assert.equal(retryWriterCalled, false);
  const again = await createIdempotencyStore({ directory }).executeOnce({
    idempotencyKey: 'po:crash-after-output',
    payload: { display_label: 'Supplier 1', total_cents: 8400 },
    write: async () => { retryWriterCalled = true; },
  });
  assert.equal(again.status, 'EXISTS');
  assert.equal(retryWriterCalled, false);
});

test('two processes contending for one key publish only one output record', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const modulePath = path.resolve(__dirname, 'idempotency.cjs');
  const key = 'po:concurrent-processes';
  const releasePath = path.join(directory, 'release-writer');
  const callbackDirectory = path.join(directory, 'callbacks');
  await fs.mkdir(callbackDirectory);
  const firstSource = `
    const fs = require('node:fs/promises');
    const path = require('node:path');
    const { createIdempotencyStore } = require(process.argv[1]);
    const directory = process.argv[2];
    const releasePath = process.argv[3];
    const callbackDirectory = process.argv[4];
    const store = createIdempotencyStore({ directory });
    const result = { display_label: 'Supplier 1', label: 'SIMULATED' };
    store.executeOnce({
      idempotencyKey: 'po:concurrent-processes', payload: { display_label: 'Supplier 1' },
      write: async ({ persistResult }) => {
        await fs.writeFile(path.join(callbackDirectory, String(process.pid)), 'called');
        while (true) {
          try { await fs.access(releasePath); break; }
          catch { await new Promise((resolve) => setTimeout(resolve, 10)); }
        }
        await persistResult(result);
        return result;
      },
    }).then((value) => process.stdout.write(JSON.stringify(value)));
  `;
  const first = runChild(firstSource, [modulePath, directory, releasePath, callbackDirectory]);
  await waitForFile(keyFile(directory, key, 'intent'));
  const second = await runChild(`
    const { createIdempotencyStore } = require(process.argv[1]);
    createIdempotencyStore({ directory: process.argv[2] }).executeOnce({
      idempotencyKey: 'po:concurrent-processes', payload: { display_label: 'Supplier 1' },
      write: async () => { throw new Error('concurrent retry must not write'); },
    }).then((value) => process.stdout.write(JSON.stringify(value)));
  `, [modulePath, directory]);
  assert.equal(JSON.parse(second.stdout).status, 'IN_PROGRESS', second.stderr);
  await fs.writeFile(releasePath, 'go');
  const firstResult = await first;
  assert.equal(JSON.parse(firstResult.stdout).status, 'CREATED', firstResult.stderr);
  assert.equal((await fs.readdir(callbackDirectory)).length, 1);

  const retry = await createIdempotencyStore({ directory }).executeOnce({
    idempotencyKey: key,
    payload: { display_label: 'Supplier 1' },
    write: async () => { throw new Error('completed retry must not write'); },
  });
  assert.equal(retry.status, 'EXISTS');
  assert.equal((await fs.readdir(directory)).filter((name) => name.endsWith('.effect.json')).length, 1);
});
