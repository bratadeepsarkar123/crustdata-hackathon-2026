'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { sampleRequests } = require('../../samples/requests.cjs');
const { createPurchaseOrderWriter } = require('./writer.cjs');
const { recordInternalSupplierName } = require('../state/internal-name-log.cjs');

const supplier = Object.freeze({
  display_label: 'Supplier 1',
  name_internal: 'INTERNAL_SENTINEL_Fictional Aster Sensor Works',
  primary_domain: 'INTERNAL_SENTINEL_aster.example',
  year_founded: 2012,
  headquarters_internal: 'INTERNAL_SENTINEL_City',
  headcount_total_internal: 120,
  industry: 'Industrial sensors',
  product_line_status: 'HUMAN_OR_SIMULATED',
  sources: Object.freeze([{ field: 'basic_info.description', endpoint: 'POST /company/enrich' }]),
  confidence: 0.82,
});

const quote = Object.freeze({
  display_label: 'Supplier 1',
  unit_price: 42,
  lead_time_days: 12,
  label: 'SIMULATED',
});

const policyDecision = Object.freeze({
  label: 'SIMULATED',
  approved: true,
  display_label: 'Supplier 1',
  reason: 'SIMULATED policy fixture approval',
});

async function makeDirectory() {
  return fs.mkdtemp(path.join(os.tmpdir(), 'contextcon-po-'));
}

async function removeDirectory(directory) {
  await fs.rm(directory, { recursive: true, force: true });
}

async function listFiles(directory) {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const target = path.join(directory, entry.name);
    return entry.isDirectory() ? listFiles(target) : [target];
  }));
  return nested.flat();
}

function flowInput(overrides = {}) {
  return {
    request: sampleRequests[0].request,
    supplier,
    quote,
    quoteCurrency: 'USD',
    policyDecision,
    ...overrides,
  };
}

test('creates separate SIMULATED vendor and PO records and reuses them on retry', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const writer = createPurchaseOrderWriter({ stateDirectory: directory });
  const first = await writer.writeVendorAndPo(flowInput());
  const repeat = await writer.writeVendorAndPo(flowInput());

  assert.equal(first.status, 'CREATED', first.errors.join('; '));

  assert.deepEqual(
    [first.status, first.vendor_status, first.po_status],
    ['CREATED', 'CREATED', 'CREATED'],
  );
  assert.deepEqual(
    [repeat.status, repeat.vendor_status, repeat.po_status],
    ['EXISTS', 'EXISTS', 'EXISTS'],
  );
  assert.ok(first.vendor_record);
  assert.ok(first.purchase_order);
  assert.notEqual(first.vendor_record.idempotency_key, first.purchase_order.idempotency_key);
  assert.notEqual(first.vendor_record.po_number, first.purchase_order.po_number);
  for (const record of [first.vendor_record, first.purchase_order]) {
    assert.deepEqual(Object.keys(record).sort(), [
      'display_label', 'idempotency_key', 'label', 'po_number', 'status', 'total',
    ]);
    assert.equal(record.display_label, 'Supplier 1');
    assert.equal(record.label, 'SIMULATED');
    assert.equal(record.status, 'SIMULATED');
    assert.equal(record.total, 21000);
  }
  assert.deepEqual(repeat.vendor_record, first.vendor_record);
  assert.deepEqual(repeat.purchase_order, first.purchase_order);

  const persistedFiles = await Promise.all((await listFiles(directory)).map((file) => fs.readFile(file, 'utf8')));
  const persisted = persistedFiles.join('\n');
  assert.ok(!persisted.includes(supplier.name_internal));
  assert.ok(!persisted.includes(supplier.primary_domain));
  assert.ok(!persisted.includes(supplier.headquarters_internal));
});

test('missing fields or a policy exception create neither a vendor record nor a PO', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const writer = createPurchaseOrderWriter({ stateDirectory: directory });
  const incomplete = {
    ...sampleRequests[2].request,
  };
  const missingResult = await writer.writeVendorAndPo(flowInput({ request: incomplete }));
  const exceptionResult = await writer.writeVendorAndPo(flowInput({
    policyDecision: { ...policyDecision, approved: false },
  }));
  assert.equal(missingResult.status, 'REJECTED');
  assert.equal(exceptionResult.status, 'REJECTED');
  assert.equal(missingResult.vendor_record, null);
  assert.equal(missingResult.purchase_order, null);
  assert.equal(exceptionResult.vendor_record, null);
  assert.equal(exceptionResult.purchase_order, null);
  assert.deepEqual(await fs.readdir(directory), []);
});

test('rejects unsafe labels, non-SIMULATED decisions, and ambiguous totals before writes', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const writer = createPurchaseOrderWriter({ stateDirectory: directory });
  const unsafeSupplier = { ...supplier, display_label: 'Aster Sensor Works' };
  const unsafeResult = await writer.writeVendorAndPo(flowInput({ supplier: unsafeSupplier }));
  const mislabeledDecision = await writer.writeVendorAndPo(flowInput({
    policyDecision: { ...policyDecision, label: 'APPROVED' },
  }));
  const ambiguousTotal = await writer.writeVendorAndPo(flowInput({
    quote: { ...quote, unit_price: 42.001 },
  }));
  assert.equal(unsafeResult.status, 'REJECTED');
  assert.equal(mislabeledDecision.status, 'REJECTED');
  assert.equal(ambiguousTotal.status, 'REJECTED');
  assert.deepEqual(await fs.readdir(directory), []);
});

test('requires explicit quote currency matching the request before any write', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const writer = createPurchaseOrderWriter({ stateDirectory: directory });
  const missing = await writer.writeVendorAndPo(flowInput({ quoteCurrency: undefined }));
  const mismatched = await writer.writeVendorAndPo(flowInput({ quoteCurrency: 'INR' }));
  assert.equal(missing.status, 'REJECTED');
  assert.equal(mismatched.status, 'REJECTED');
  assert.equal(missing.vendor_record, null);
  assert.equal(missing.purchase_order, null);
  assert.equal(mismatched.vendor_record, null);
  assert.equal(mismatched.purchase_order, null);
  assert.deepEqual(await fs.readdir(directory), []);
});

test('same request key with a changed supplier payload is rejected without another record', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const writer = createPurchaseOrderWriter({ stateDirectory: directory });
  const first = await writer.writeVendorAndPo(flowInput());
  const before = await fs.readdir(directory);
  const changedSupplier = { ...supplier, name_internal: 'INTERNAL_SENTINEL_Different Fictional Supplier' };
  const collision = await writer.writeVendorAndPo(flowInput({ supplier: changedSupplier }));
  const after = await fs.readdir(directory);
  assert.equal(first.status, 'CREATED');
  assert.equal(collision.status, 'KEY_CONFLICT');
  assert.equal(collision.vendor_record, null);
  assert.equal(collision.purchase_order, null);
  assert.deepEqual(after.sort(), before.sort());
});

test('only the explicit internal name log stores supplier names', async (t) => {
  const directory = await makeDirectory();
  t.after(() => removeDirectory(directory));
  const logDirectory = path.join(directory, 'internal-name-log');
  const result = await recordInternalSupplierName(supplier, { directory: logDirectory });
  assert.equal(result.status, 'CREATED');
  assert.equal(result.display_label, supplier.display_label);
  const content = (await Promise.all((await listFiles(logDirectory)).map((file) => fs.readFile(file, 'utf8')))).join('\n');
  assert.ok(content.includes(supplier.name_internal));
  assert.ok(!content.includes(supplier.primary_domain));
  assert.ok(!content.includes(supplier.headquarters_internal));
});
