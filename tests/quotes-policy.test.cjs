'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const {
  buildSimulatedQuote,
  buildOneItemQuote,
  ONE_ITEM_QUOTE,
  rankQuotes,
} = require('../src/quotes/quote.cjs');
const { validateQuote } = require('../src/contracts/index.cjs');
const {
  checkPolicy,
  evaluatePolicyDecision,
  evaluateQuotesPolicy,
} = require('../src/policy/policy.cjs');
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

test('retries with the same inputs return the same purchase order number and handles key conflict', async (t) => {
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
  assert.equal(first.status, 'CREATED');
  assert.ok(first.purchase_order.po_number);

  const retry = await writer.writeVendorAndPo(inputs);
  assert.equal(retry.status, 'EXISTS');
  assert.equal(retry.purchase_order.po_number, first.purchase_order.po_number);

  const conflictInputs = {
    ...inputs,
    quote: {
      ...inputs.quote,
      unit_price: 45,
    },
  };
  const conflict = await writer.writeVendorAndPo(conflictInputs);
  assert.equal(conflict.status, 'KEY_CONFLICT');
  assert.equal(conflict.purchase_order, null);
});

test('one-item quote builder conforms to validateQuote with neutral label and SIMULATED flag', () => {
  const quote = buildOneItemQuote();
  assert.deepEqual(quote, {
    display_label: 'Supplier 1',
    unit_price: 1.25,
    lead_time_days: 7,
    label: 'SIMULATED',
  });
  const check = validateQuote(quote);
  assert.equal(check.valid, true);
  assert.equal(check.errors.length, 0);

  const staticCheck = validateQuote(ONE_ITEM_QUOTE);
  assert.equal(staticCheck.valid, true);
  assert.equal(staticCheck.errors.length, 0);
});

test('one-item policy evaluation handles approve, hold (MOQ not verified), and reject', () => {
  const request = {
    item: 'neodymium speaker magnet, 3 mm thick',
    quantity: 1000,
    budget: 2500,
    currency: 'USD',
    deadline_days: 14,
    region: 'US',
    missing_fields: [],
  };
  const quote = buildOneItemQuote(); // unit_price: 1.25, total: 1250, lead_time: 7

  // P1: When options is omitted, it MUST return HOLD (not APPROVE)
  const defaultOptionsDecision = evaluatePolicyDecision({
    request,
    quote,
  });
  assert.equal(defaultOptionsDecision.status, 'HOLD');
  assert.equal(defaultOptionsDecision.approved, false);
  assert.equal(defaultOptionsDecision.reason, 'HOLD: MOQ not verified');

  // 1. Explicit Hold on unverified MOQ
  const holdDecision = evaluatePolicyDecision({
    request,
    quote,
    options: { moq_verified: false },
  });
  assert.equal(holdDecision.status, 'HOLD');
  assert.equal(holdDecision.approved, false);
  assert.equal(holdDecision.display_label, 'Supplier 1');
  assert.equal(holdDecision.reason, 'HOLD: MOQ not verified');
  assert.equal(holdDecision.label, 'SIMULATED');

  // 2. Approve when compliant AND MOQ is explicitly confirmed
  const approveDecision = evaluatePolicyDecision({
    request,
    quote,
    options: { moq_verified: true },
  });
  assert.equal(approveDecision.status, 'APPROVE');
  assert.equal(approveDecision.approved, true);
  assert.equal(approveDecision.display_label, 'Supplier 1');
  assert.match(approveDecision.reason, /within budget/);

  // 3. Reject when over budget even if MOQ is confirmed
  const rejectDecision = evaluatePolicyDecision({
    request: { ...request, budget: 1000 }, // 1250 > 1000
    quote,
    options: { moq_verified: true },
  });
  assert.equal(rejectDecision.status, 'REJECT');
  assert.equal(rejectDecision.approved, false);
  assert.match(rejectDecision.reason, /over the budget/);
});

test('rankQuotes validates every quote and rejects bad labels or private fields', () => {
  const validQuotes = [
    { display_label: 'Supplier 2', unit_price: 2.0, lead_time_days: 10, label: 'SIMULATED' },
    { display_label: 'Supplier 1', unit_price: 1.25, lead_time_days: 7, label: 'SIMULATED' },
  ];

  const ranked = rankQuotes(validQuotes, { quantity: 1000 });
  assert.equal(ranked.length, 2);
  assert.equal(ranked[0].display_label, 'Supplier 1');
  assert.equal(ranked[1].display_label, 'Supplier 2');

  // Reject bad display label
  assert.throws(
    () => rankQuotes([{ display_label: 'Bad Vendor Name', unit_price: 1.0, lead_time_days: 5, label: 'SIMULATED' }]),
    /Invalid quote in rankQuotes/
  );

  // Reject quote containing private fields
  assert.throws(
    () => rankQuotes([{
      display_label: 'Supplier 1',
      unit_price: 1.0,
      lead_time_days: 5,
      label: 'SIMULATED',
      name_internal: 'Confidential Corp',
    }]),
    /Invalid quote in rankQuotes/
  );
});

test('evaluateQuotesPolicy validates quotes and never leaks private fields', () => {
  const request = {
    item: 'sensor',
    quantity: 100,
    budget: 5000,
    currency: 'USD',
    deadline_days: 14,
    region: 'US',
    missing_fields: [],
  };

  // Rejects quote with private field
  assert.throws(
    () => evaluateQuotesPolicy({
      request,
      quotes: [{
        display_label: 'Supplier 1',
        unit_price: 10,
        lead_time_days: 5,
        label: 'SIMULATED',
        raw_company_name: 'Secret Supplier LLC',
      }],
    }),
    /Invalid quote in evaluateQuotesPolicy/
  );

  // Compliant quote result contains only contract keys
  const result = evaluateQuotesPolicy({
    request,
    quotes: [
      { display_label: 'Supplier 1', unit_price: 10, lead_time_days: 5, label: 'SIMULATED' },
    ],
  });

  assert.equal(result.approved_candidates.length, 1);
  const candidate = result.approved_candidates[0];
  assert.deepEqual(Object.keys(candidate.quote), ['display_label', 'unit_price', 'lead_time_days', 'label']);
  assert.equal(candidate.quote.name_internal, undefined);
  assert.equal(candidate.quote.raw_company_name, undefined);
});

test('held sample must not have a purchase order (fails if HOLD has a CREATED order)', () => {
  const samplePath = path.resolve(__dirname, '../samples/one-item/neutral-output.json');
  const sample = JSON.parse(fs.readFileSync(samplePath, 'utf8'));

  // 1. Verify neutral-output.json enforces purchase_order: null when held
  assert.equal(sample.policy_evaluation.status, 'HOLD');
  assert.equal(sample.purchase_order, null);
  assert.equal(sample.purchase_order_status, 'NOT_ATTEMPTED_WHILE_HELD');
  assert.ok(sample.hypothetical_confirmed_case);
  assert.ok(sample.hypothetical_confirmed_case.purchase_order);

  // 2. Regression guard: a validator rule asserting HOLD sample cannot have a CREATED purchase_order
  function validateSampleIntegrity(data) {
    if (data.policy_evaluation && data.policy_evaluation.status === 'HOLD' && data.purchase_order !== null) {
      throw new Error('Invalid sample: a held quote cannot have an issued purchase order');
    }
    return true;
  }

  assert.equal(validateSampleIntegrity(sample), true);

  // Assert it throws on regression (HOLD + CREATED purchase order)
  const regressionSample = {
    ...sample,
    purchase_order: {
      po_number: 'SIM-PO-MAGNET-001',
      status: 'CREATED',
    },
  };
  assert.throws(
    () => validateSampleIntegrity(regressionSample),
    /Invalid sample: a held quote cannot have an issued purchase order/
  );
});
