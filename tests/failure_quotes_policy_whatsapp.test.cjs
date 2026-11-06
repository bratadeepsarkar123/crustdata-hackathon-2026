'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { buildSimulatedQuote, loadSimulatedQuotes, rankQuotes } = require('../src/quotes/quote.cjs');
const { checkPolicy, evaluateQuotesPolicy } = require('../src/policy/policy.cjs');
const {
  buildTeamPhoneMessage,
  buildSimulatedWhatsAppMessage,
  createWhatsAppSender,
} = require('../src/whatsapp/team-phone.cjs');
const { createPurchaseOrderWriter } = require('../src/po/writer.cjs');
const fullFlowFixture = require('../samples/full-flow.cjs');

test('WhatsApp module guard refuses unauthorized modes (e.g., LIVE, EXTERNAL)', () => {
  assert.throws(
    () => createWhatsAppSender({ mode: 'LIVE' }),
    /Refused: WhatsApp module refuses to run unless mode is TEAM_PHONE or SIMULATED/
  );
  assert.throws(
    () => createWhatsAppSender({ mode: 'SUPPLIER_DIRECT' }),
    /Refused: WhatsApp module refuses to run unless mode is TEAM_PHONE or SIMULATED/
  );
});

test('WhatsApp module in TEAM_PHONE mode asserts no outbound call to unlisted numbers', () => {
  const teamPhones = ['+919876543210', '+919123456789'];
  const sender = createWhatsAppSender({ mode: 'TEAM_PHONE', teamPhones });

  // Attempting to send to an unlisted external supplier number must fail hard
  assert.throws(
    () =>
      sender.send({
        displayLabel: 'Supplier 1',
        text: 'Request for Quotation: 500 Industrial Temperature Sensors',
        idempotencyKey: 'rfq-supplier-1-unauthorized',
        toNumber: '+19998887777', // outside number
      }),
    /Refused: WhatsApp messages may only go to team phones/
  );

  // Assert no calls were logged
  assert.equal(sender.getRawNetworkCallLog().length, 0);

  // Sending to a registered team phone succeeds
  const sent = sender.send({
    displayLabel: 'Supplier 1',
    text: 'Request for Quotation: 500 Industrial Temperature Sensors',
    idempotencyKey: 'rfq-supplier-1-allowed',
    toNumber: '+919876543210',
  });
  assert.equal(sent.success, true);
  assert.equal(sent.message.mode, 'TEAM_PHONE');
  assert.equal(sender.getRawNetworkCallLog().length, 1);
});

test('repeated WhatsApp send with the same key sends once (idempotent replay)', () => {
  const sender = createWhatsAppSender({ mode: 'SIMULATED' });
  const idempotencyKey = 'rfq-send-sensor-500-supplier-1';

  const firstAttempt = sender.send({
    displayLabel: 'Supplier 1',
    text: 'Please provide unit price and lead time for 500 units',
    idempotencyKey,
  });

  assert.equal(firstAttempt.success, true);
  assert.equal(firstAttempt.replayed, false);
  assert.equal(firstAttempt.send_count, 1);
  assert.equal(firstAttempt.message.label, 'SIMULATED');

  // Retry with the exact same key
  const secondAttempt = sender.send({
    displayLabel: 'Supplier 1',
    text: 'Please provide unit price and lead time for 500 units',
    idempotencyKey,
  });

  assert.equal(secondAttempt.success, true);
  assert.equal(secondAttempt.replayed, true);
  assert.equal(secondAttempt.send_count, 1);
  assert.deepEqual(secondAttempt.message, firstAttempt.message);
  assert.equal(sender.getSentRecords().length, 1);
});

test('policy evaluation routes an over-budget quote to exceptions queue with reason', () => {
  const request = {
    item: 'industrial temperature sensor',
    quantity: 500,
    budget: 25000,
    currency: 'USD',
    deadline_days: 14,
    region: 'North America',
    missing_fields: [],
  };

  const quotes = [
    { display_label: 'Supplier 1', unit_price: 42, lead_time_days: 10, label: 'SIMULATED' }, // 42 * 500 = $21,000 <= 25,000 (Compliant)
    { display_label: 'Supplier 2', unit_price: 55, lead_time_days: 12, label: 'SIMULATED' }, // 55 * 500 = $27,500 > 25,000 (Over budget)
    { display_label: 'Supplier 3', unit_price: 40, lead_time_days: 18, label: 'SIMULATED' }, // 18 > 14 (Delivery deadline exceeded)
  ];

  const evaluation = evaluateQuotesPolicy({ request, quotes });

  assert.equal(evaluation.label, 'SIMULATED');
  assert.equal(evaluation.approved_candidates.length, 1);
  assert.equal(evaluation.best_candidate.display_label, 'Supplier 1');

  // Assert exceptions queue captures non-compliant quotes with clear reasons
  assert.equal(evaluation.exceptions_queue.length, 2);

  const overBudgetException = evaluation.exceptions_queue.find(
    (e) => e.display_label === 'Supplier 2'
  );
  assert.ok(overBudgetException);
  assert.match(overBudgetException.reason, /total 27500 is over the budget of 25000/);

  const leadTimeException = evaluation.exceptions_queue.find(
    (e) => e.display_label === 'Supplier 3'
  );
  assert.ok(leadTimeException);
  assert.match(leadTimeException.reason, /lead time 18 days is over the 14-day deadline/);
});

test('quotes and ranked results show labels only without leaking private names', () => {
  const loadedQuotes = loadSimulatedQuotes();
  assert.ok(loadedQuotes.length >= 2);

  for (const quote of loadedQuotes) {
    assert.match(quote.display_label, /^Supplier [1-9]\d*$/);
    assert.equal(quote.label, 'SIMULATED');
    // Ensure no unmasked internal properties exist
    assert.equal(quote.name_internal, undefined);
    assert.equal(quote.raw_vendor_name, undefined);
  }

  const ranked = rankQuotes(loadedQuotes, { quantity: 500 });
  for (const item of ranked) {
    assert.match(item.display_label, /^Supplier [1-9]\d*$/);
    assert.equal(item.label, 'SIMULATED');
    assert.equal(item.name_internal, undefined);
  }
});

test('PO retries with the same inputs return the same purchase order and do not duplicate', async (t) => {
  const stateDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'failure-po-retry-'));
  t.after(() => fs.rmSync(stateDirectory, { recursive: true, force: true }));

  const writer = createPurchaseOrderWriter({ stateDirectory });
  const inputs = {
    request: fullFlowFixture.request,
    supplier: fullFlowFixture.suppliers[0],
    quote: fullFlowFixture.quotes[0],
    quoteCurrency: fullFlowFixture.quote_currency_by_label['Supplier 1'],
    policyDecision: fullFlowFixture.policy_decision,
  };

  const run1 = await writer.writeVendorAndPo(inputs);
  const run2 = await writer.writeVendorAndPo(inputs);

  assert.equal(run1.purchase_order.po_number, run2.purchase_order.po_number);
  assert.equal(run1.vendor_record.po_number, run2.vendor_record.po_number);
  assert.equal(run2.status, 'EXISTS');
});
