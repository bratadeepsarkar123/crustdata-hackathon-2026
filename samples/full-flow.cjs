'use strict';

const { sampleRequests } = require('./requests.cjs');
const { discoveryCandidates } = require('../src/discovery/index.cjs');

const policyDecision = Object.freeze({
  label: 'SIMULATED',
  approved: true,
  display_label: 'Supplier 1',
  reason: 'SIMULATED fixture policy decision: this quote is within the sample request budget and delivery window.',
});

const fullFlowFixture = Object.freeze({
  label: 'SIMULATED',
  request_text: sampleRequests[0].text,
  request: sampleRequests[0].request,
  suppliers: discoveryCandidates,
  quote_currency_by_label: Object.freeze({
    'Supplier 1': 'USD',
    'Supplier 2': 'USD',
  }),
  quotes: Object.freeze([
    Object.freeze({ display_label: 'Supplier 1', unit_price: 42, lead_time_days: 12, label: 'SIMULATED' }),
    Object.freeze({ display_label: 'Supplier 2', unit_price: 53, lead_time_days: 20, label: 'SIMULATED' }),
  ]),
  policy_decision: policyDecision,
  chosen_supplier_label: policyDecision.display_label,
});

module.exports = fullFlowFixture;
