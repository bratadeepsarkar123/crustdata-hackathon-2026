'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { buildSimulatedQuote } = require('../src/quotes/quote.cjs');
const { checkPolicy } = require('../src/policy/policy.cjs');
const { buildTeamPhoneMessage } = require('../src/whatsapp/team-phone.cjs');
const { createPurchaseOrderWriter } = require('../src/po/writer.cjs');
const fullFlowFixture = require('../samples/full-flow.cjs');

test('simulated quotes are labelled and reject invalid prices or labels', () => {
  const quote = buildSimulatedQuote({
    displayLabel: 'Supplier 1',
    unitPrice: 42,
    leadTimeDays: 12,
  });

  assert.equal(quote.label, 'SIMULATED');
  assert.throws(() => buildSimulatedQuote({
    displayLabel: 'Supplier 1',
    unitPrice: -1,
    leadTimeDays: 12,
  }));
  assert.throws(() => buildSimulatedQuote({
    displayLabel: 'Vendor 1',
    unitPrice: 42,
    leadTimeDays: 12,
  }));
});

test('policy checks enforce budget and delivery deadline', () => {
  const request = { quantity: 500, budget: 25000, deadline_days: 14 };
  const withinPolicy = checkPolicy({
    request,
    quote: { display_label: 'Supplier 1', unit_price: 42, lead_time_days: 12 },
  });
  const overBudget = checkPolicy({
    request,
    quote: { display_label: 'Supplier 1', unit_price: 53, lead_time_days: 12 },
  });
  const tooSlow = checkPolicy({
    request,
    quote: { display_label: 'Supplier 1', unit_price: 42, lead_time_days: 20 },
  });

  assert.equal(withinPolicy.approved, true);
  assert.equal(overBudget.approved, false);
  assert.equal(tooSlow.approved, false);
});

test('team phone messages reject unlisted numbers and mark allowed messages', () => {
  const message = {
    displayLabel: 'Supplier 1',
    text: 'Quote is ready.',
    idempotencyKey: 'quote-ready-1',
    toNumber: '+15550000001',
    teamPhones: ['+15550000002'],
  };

  assert.throws(() => buildTeamPhoneMessage(message));

  const allowed = buildTeamPhoneMessage({
    ...message,
    toNumber: '+15550000002',
  });
  assert.equal(allowed.mode, 'TEAM_PHONE');
});

test('retries with the same inputs return the same purchase order number', async (t) => {
  const stateDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'quotes-policy-po-'));
  t.after(() => fs.rmSync(stateDirectory, { recursive: true, force: true }));

  const writer = createPurchaseOrderWriter({ stateDirectory });
  const inputs = {
    request: fullFlowFixture.request,
    supplier: fullFlowFixture.suppliers[0],
    quote: fullFlowFixture.quotes[0],
    quoteCurrency: fullFlowFixture.quote_currency_by_label['Supplier 1'],
    policyDecision: fullFlowFixture.policy_decision,
  };

  const first = await writer.writeVendorAndPo(inputs);
  const retry = await writer.writeVendorAndPo(inputs);

  assert.ok(first.purchase_order.po_number);
  assert.equal(retry.purchase_order.po_number, first.purchase_order.po_number);
});
