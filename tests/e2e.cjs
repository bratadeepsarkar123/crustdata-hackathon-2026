'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const https = require('node:https');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { parseRequest } = require('../src/intake/request-reader.cjs');
const { runOfflineFixture, safeStateDirectory } = require('../src/orchestrator.cjs');
const fullFlowFixture = require('../samples/full-flow.cjs');
const { sampleRequests } = require('../samples/requests.cjs');

function makeStateDirectory(t) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'contextcon-e2e-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  return directory;
}

function blockNetwork(t) {
  const oldFetch = globalThis.fetch;
  const oldHttpRequest = http.request;
  const oldHttpGet = http.get;
  const oldHttpsRequest = https.request;
  const oldHttpsGet = https.get;
  const denied = () => { throw new Error('Network use is forbidden in offline fixture tests'); };
  globalThis.fetch = denied;
  http.request = denied;
  http.get = denied;
  https.request = denied;
  https.get = denied;
  t.after(() => {
    globalThis.fetch = oldFetch;
    http.request = oldHttpRequest;
    http.get = oldHttpGet;
    https.request = oldHttpsRequest;
    https.get = oldHttpsGet;
  });
}

function completeFileCount(directory) {
  if (!fs.existsSync(directory)) return 0;
  return fs.readdirSync(directory).filter((name) => name.endsWith('.complete.json')).length;
}

test('all three sample texts parse to their exact expected requests', () => {
  assert.equal(sampleRequests.length, 3);
  for (const sample of sampleRequests) {
    assert.equal(sample.label, 'SIMULATED');
    assert.deepEqual(parseRequest(sample.text), sample.request);
  }
  assert.equal(sampleRequests[2].request.deadline_days, null);
  assert.deepEqual(sampleRequests[2].request.missing_fields, ['deadline_days']);
});

test('offline fixture completes stages 1–7 with citations and no network', async (t) => {
  blockNetwork(t);
  const stateDirectory = makeStateDirectory(t);
  const output = await runOfflineFixture({ stateDirectory });

  assert.equal(output.label, 'SIMULATED');
  assert.equal(output.mode, 'OFFLINE_FIXTURE_ONLY');
  assert.deepEqual(output.steps.map(({ step }) => step), [1, 2, 3, 4, '5a', '5b', 6, 7]);
  assert.ok(output.steps.every((step) => step.label === 'SIMULATED'));
  assert.match(output.steps[1].source, /SIMULATED fixture/);
  assert.match(output.steps[2].source, /SIMULATED fixture/);
  assert.match(output.steps[3].source, /SIMULATED fixture/);
  assert.match(output.steps[4].source, /No message was sent/);
  assert.match(output.steps[5].source, /SIMULATED fixture/);
  assert.match(output.steps[6].source, /SIMULATED fixture/);
  assert.equal(output.request_label, 'SIMULATED');
  assert.deepEqual(output.request, sampleRequests[0].request);
  assert.equal(output.policy_decision.label, 'SIMULATED');
  assert.equal(output.policy_decision.display_label, fullFlowFixture.chosen_supplier_label);
  assert.equal(output.quotes.length, 2);
  assert.ok(output.quotes.every((quote) => quote.label === 'SIMULATED' && quote.currency === 'USD'));
  assert.ok(output.quotes.every((quote) => quote.source === 'SIMULATED fixture; no live Crustdata call'));
  assert.ok(output.quotes.every((quote) => quote.quote.label === 'SIMULATED'));
  assert.equal(output.vendor_record.label, 'SIMULATED');
  assert.equal(output.vendor_record.currency, 'USD');
  assert.equal(output.vendor_record.source, 'SIMULATED local writer');
  assert.equal(output.vendor_record.record.label, 'SIMULATED');
  assert.equal(output.purchase_order.label, 'SIMULATED');
  assert.equal(output.purchase_order.currency, 'USD');
  assert.equal(output.purchase_order.source, 'SIMULATED local writer');
  assert.equal(output.purchase_order.record.label, 'SIMULATED');
  assert.notEqual(output.vendor_record.record.idempotency_key, output.purchase_order.record.idempotency_key);

  for (const card of output.suppliers) {
    assert.deepEqual(Object.keys(card).sort(), ['display_label', 'label', 'sources']);
    assert.equal(card.label, 'SIMULATED');
    assert.match(card.display_label, /^Supplier \d+$/);
    assert.ok(card.sources.length > 0);
    for (const citation of card.sources) {
      assert.equal(citation.source, 'SIMULATED fixture; no live Crustdata call');
      assert.ok(citation.field.length > 0);
      assert.match(citation.endpoint, /^POST \/company\/(identify|enrich)$/);
    }
  }
  const serialized = JSON.stringify(output);
  for (const privateValue of [
    'Fictional Aster Sensor Works',
    'Fictional Bluebell Instrument Works',
    'aster-sensor-works.example',
    'bluebell-instrument-works.example',
    'Vadodara',
    'Mysuru',
  ]) assert.equal(serialized.includes(privateValue), false);
  assert.equal(serialized.includes('name_internal'), false);
  assert.equal(completeFileCount(stateDirectory), 2);
});

test('repeating the same flow reuses exactly one vendor and one PO', async (t) => {
  const stateDirectory = makeStateDirectory(t);
  const first = await runOfflineFixture({ stateDirectory });
  const second = await runOfflineFixture({ stateDirectory });

  assert.deepEqual(second.vendor_record, first.vendor_record);
  assert.deepEqual(second.purchase_order, first.purchase_order);
  assert.equal(second.steps[7].vendor_status, 'EXISTS');
  assert.equal(second.steps[7].po_status, 'EXISTS');
  assert.equal(completeFileCount(stateDirectory), 2);
});

test('missing and ambiguous requests reject before creating state or records', async (t) => {
  const missingState = path.join(os.tmpdir(), `contextcon-missing-${process.pid}-${Date.now()}`);
  const ambiguousState = path.join(os.tmpdir(), `contextcon-ambiguous-${process.pid}-${Date.now()}`);
  t.after(() => {
    fs.rmSync(missingState, { recursive: true, force: true });
    fs.rmSync(ambiguousState, { recursive: true, force: true });
  });

  await assert.rejects(
    runOfflineFixture({ requestText: sampleRequests[2].text, stateDirectory: missingState }),
    (error) => error.code === 'MISSING_REQUEST_FIELDS',
  );
  await assert.rejects(
    runOfflineFixture({ requestText: 'Need 500 industrial temperature sensors in Bengaluru or Pune, perhaps within 14 or 30 days.', stateDirectory: ambiguousState }),
    (error) => error.code === 'REQUEST_NOT_IN_FIXTURES',
  );
  assert.equal(fs.existsSync(missingState), false);
  assert.equal(fs.existsSync(ambiguousState), false);
});

test('fixture request mismatch rejects before creating state or records', async (t) => {
  const stateDirectory = path.join(os.tmpdir(), `contextcon-fixture-mismatch-${process.pid}-${Date.now()}`);
  t.after(() => fs.rmSync(stateDirectory, { recursive: true, force: true }));
  const fixture = structuredClone(fullFlowFixture);
  fixture.request.budget += 1;

  await assert.rejects(
    runOfflineFixture({ fixture, stateDirectory }),
    (error) => error.code === 'FIXTURE_REQUEST_MISMATCH',
  );
  assert.equal(fs.existsSync(stateDirectory), false);
});

test('a failed simulated policy gate creates no vendor or PO', async (t) => {
  const stateDirectory = path.join(os.tmpdir(), `contextcon-policy-${process.pid}-${Date.now()}`);
  t.after(() => fs.rmSync(stateDirectory, { recursive: true, force: true }));
  const fixture = structuredClone(fullFlowFixture);
  fixture.policy_decision.approved = false;

  await assert.rejects(
    runOfflineFixture({ fixture, stateDirectory }),
    (error) => error.code === 'POLICY_NOT_APPROVED',
  );
  assert.equal(fs.existsSync(stateDirectory), false);
});

test('invalid or mismatched supplier/quote fixture rejects before writing', async (t) => {
  const stateDirectory = path.join(os.tmpdir(), `contextcon-quote-mismatch-${process.pid}-${Date.now()}`);
  t.after(() => fs.rmSync(stateDirectory, { recursive: true, force: true }));
  const fixture = structuredClone(fullFlowFixture);
  fixture.quotes[0].display_label = 'Supplier 9';

  await assert.rejects(
    runOfflineFixture({ fixture, stateDirectory }),
    (error) => error.code === 'UNSAFE_FIXTURE',
  );
  assert.equal(fs.existsSync(stateDirectory), false);
});

test('missing or mismatched quote currency rejects before writing', async (t) => {
  const missingState = path.join(os.tmpdir(), `contextcon-no-quote-currency-${process.pid}-${Date.now()}`);
  const mismatchedState = path.join(os.tmpdir(), `contextcon-quote-currency-${process.pid}-${Date.now()}`);
  t.after(() => {
    fs.rmSync(missingState, { recursive: true, force: true });
    fs.rmSync(mismatchedState, { recursive: true, force: true });
  });
  const missingCurrency = structuredClone(fullFlowFixture);
  delete missingCurrency.quote_currency_by_label['Supplier 2'];
  await assert.rejects(
    runOfflineFixture({ fixture: missingCurrency, stateDirectory: missingState }),
    (error) => error.code === 'UNSAFE_FIXTURE',
  );

  const mismatchedCurrency = structuredClone(fullFlowFixture);
  mismatchedCurrency.quote_currency_by_label['Supplier 1'] = 'INR';
  await assert.rejects(
    runOfflineFixture({ fixture: mismatchedCurrency, stateDirectory: mismatchedState }),
    (error) => error.code === 'QUOTE_CURRENCY_MISMATCH',
  );
  assert.equal(fs.existsSync(missingState), false);
  assert.equal(fs.existsSync(mismatchedState), false);
});

test('supplier internals and policy reason stay hidden; injected citation URL is rejected', async (t) => {
  const stateDirectory = makeStateDirectory(t);
  const fixture = structuredClone(fullFlowFixture);
  fixture.suppliers[0].name_internal = 'LEAK_NAME_SENTINEL';
  fixture.suppliers[0].primary_domain = 'LEAK_DOMAIN_SENTINEL.example';
  fixture.suppliers[0].headquarters_internal = 'LEAK_HQ_SENTINEL';
  fixture.suppliers[0].headcount_total_internal = 987654321;
  fixture.policy_decision.reason = 'LEAK_REASON_SENTINEL';
  const output = await runOfflineFixture({ fixture, stateDirectory });
  const serialized = JSON.stringify(output);
  for (const sentinel of ['LEAK_NAME_SENTINEL', 'LEAK_DOMAIN_SENTINEL', 'LEAK_HQ_SENTINEL', '987654321', 'LEAK_REASON_SENTINEL']) {
    assert.equal(serialized.includes(sentinel), false);
  }

  const poisonedState = path.join(os.tmpdir(), `contextcon-poisoned-${process.pid}-${Date.now()}`);
  t.after(() => fs.rmSync(poisonedState, { recursive: true, force: true }));
  const poisonedFixture = structuredClone(fullFlowFixture);
  poisonedFixture.suppliers[0].sources[0].endpoint = 'https://evil.test/enrich?name=INTERNAL_NAME_SENTINEL';
  await assert.rejects(
    runOfflineFixture({ fixture: poisonedFixture, stateDirectory: poisonedState }),
    (error) => error.code === 'UNSAFE_FIXTURE',
  );
  assert.equal(fs.existsSync(poisonedState), false);
});

test('unsafe state paths outside the OS temporary directory are rejected', async () => {
  await assert.rejects(
    runOfflineFixture({ stateDirectory: path.resolve(__dirname, '..', 'unsafe-state') }),
    (error) => error.code === 'UNSAFE_STATE_DIRECTORY',
  );
});

test('a non-existent nested path under the OS temporary directory is safe', () => {
  const nested = path.join(os.tmpdir(), `contextcon-uncreated-${process.pid}-${Date.now()}`, 'state');
  assert.equal(safeStateDirectory(nested), path.resolve(nested));
  assert.equal(fs.existsSync(nested), false);
});
