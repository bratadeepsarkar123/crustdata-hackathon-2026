'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { createPurchaseOrderWriter } = require('../src/po/writer.cjs');
const { createIdempotencyStore } = require('../src/state/idempotency.cjs');
const fullFlowFixture = require('../samples/full-flow.cjs');

async function makeTempDir() {
  return fs.mkdtemp(path.join(os.tmpdir(), 'one-item-po-test-'));
}

async function removeTempDir(directory) {
  await fs.rm(directory, { recursive: true, force: true });
}

test('one-item PO line creation, idempotent retry, and KEY_CONFLICT using createPurchaseOrderWriter', async (t) => {
  const stateDirectory = await makeTempDir();
  t.after(() => removeTempDir(stateDirectory));

  const writer = createPurchaseOrderWriter({ stateDirectory });
  const inputs = {
    request: fullFlowFixture.request,
    supplier: fullFlowFixture.suppliers[0],
    quote: fullFlowFixture.quotes[0],
    quoteCurrency: fullFlowFixture.quote_currency_by_label['Supplier 1'],
    policyDecision: fullFlowFixture.policy_decision,
  };

  // 1. Initial creation returns CREATED
  const first = await writer.writeVendorAndPo(inputs);
  assert.equal(first.status, 'CREATED');
  assert.equal(first.vendor_status, 'CREATED');
  assert.equal(first.po_status, 'CREATED');
  assert.ok(first.purchase_order);
  assert.ok(first.purchase_order.po_number);
  assert.ok(first.purchase_order.idempotency_key);
  assert.equal(first.purchase_order.display_label, 'Supplier 1');
  assert.equal(first.purchase_order.total, 21000);

  // 2. Re-running with SAME key and same payload returns status: EXISTS
  const retry = await writer.writeVendorAndPo(inputs);
  assert.equal(retry.status, 'EXISTS');
  assert.equal(retry.vendor_status, 'EXISTS');
  assert.equal(retry.po_status, 'EXISTS');
  assert.ok(retry.purchase_order);
  assert.equal(retry.purchase_order.po_number, first.purchase_order.po_number);
  assert.equal(retry.purchase_order.idempotency_key, first.purchase_order.idempotency_key);
  assert.deepEqual(retry.purchase_order, first.purchase_order);

  // 3. Re-running with SAME key but a DIFFERENT payload returns status: KEY_CONFLICT
  // The request is unchanged (same idempotency key suffix), but the quote unit_price is changed.
  const conflictInputs = {
    ...inputs,
    quote: {
      ...inputs.quote,
      unit_price: 45,
    },
  };
  const conflict = await writer.writeVendorAndPo(conflictInputs);
  assert.equal(conflict.status, 'KEY_CONFLICT');
  assert.equal(conflict.vendor_status, 'KEY_CONFLICT');
  assert.equal(conflict.po_status, 'NOT_ATTEMPTED');
  assert.equal(conflict.vendor_record, null);
  assert.equal(conflict.purchase_order, null);
});

test('one-item PO line idempotency and KEY_CONFLICT using createIdempotencyStore', async (t) => {
  const stateDirectory = await makeTempDir();
  t.after(() => removeTempDir(stateDirectory));

  const store = createIdempotencyStore({ directory: stateDirectory });
  const idempotencyKey = 'po:line:item:500-industrial-temp-sensors';

  const poPayload = {
    line_item: 'industrial temperature sensors',
    quantity: 500,
    unit_price: 42,
    total: 21000,
    currency: 'USD',
    supplier: 'Supplier 1',
  };

  const writePoLine = (record) => async ({ persistResult }) => {
    await persistResult(record);
    return record;
  };

  const poRecord = {
    po_number: 'SIM-PO-LINE-001',
    line_item: poPayload.line_item,
    quantity: poPayload.quantity,
    unit_price: poPayload.unit_price,
    total: poPayload.total,
    currency: poPayload.currency,
    supplier: poPayload.supplier,
    status: 'SIMULATED',
  };

  // 1. Initial creation returns CREATED
  const first = await store.executeOnce({
    idempotencyKey,
    payload: poPayload,
    write: writePoLine(poRecord),
  });
  assert.equal(first.status, 'CREATED');
  assert.deepEqual(first.result, poRecord);

  // 2. Re-running with SAME key and same payload returns status: EXISTS
  const retry = await store.executeOnce({
    idempotencyKey,
    payload: poPayload,
    write: writePoLine(poRecord),
  });
  assert.equal(retry.status, 'EXISTS');
  assert.deepEqual(retry.result, poRecord);

  // 3. Re-running with SAME key but a DIFFERENT payload returns status: KEY_CONFLICT
  const modifiedPayload = {
    ...poPayload,
    unit_price: 45,
    total: 22500,
  };
  const conflict = await store.executeOnce({
    idempotencyKey,
    payload: modifiedPayload,
    write: writePoLine({
      ...poRecord,
      unit_price: 45,
      total: 22500,
    }),
  });
  assert.equal(conflict.status, 'KEY_CONFLICT');
  assert.equal(conflict.result, undefined);
});
