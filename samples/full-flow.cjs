'use strict';

const { sampleRequests } = require('./requests.cjs');

const supplierOne = Object.freeze({
  display_label: 'Supplier 1',
  name_internal: 'SIMULATED Fictional Aster Sensor Works',
  primary_domain: 'aster-sensor-works.example',
  year_founded: 2012,
  headquarters_internal: 'Vadodara',
  headcount_total_internal: 120,
  industry: 'Industrial sensors',
  product_line_status: 'HUMAN_OR_SIMULATED',
  sources: Object.freeze([
    Object.freeze({ field: 'primary_domain', endpoint: 'POST /company/identify' }),
    Object.freeze({ field: 'year_founded', endpoint: 'POST /company/enrich' }),
    Object.freeze({ field: 'headcount.total', endpoint: 'POST /company/enrich' }),
    Object.freeze({ field: 'locations.headquarters', endpoint: 'POST /company/enrich' }),
    Object.freeze({ field: 'basic_info.description', endpoint: 'POST /company/enrich' }),
  ]),
  confidence: 0.82,
});

const supplierTwo = Object.freeze({
  display_label: 'Supplier 2',
  name_internal: 'SIMULATED Fictional Bluebell Instrument Works',
  primary_domain: 'bluebell-instrument-works.example',
  year_founded: 2016,
  headquarters_internal: 'Mysuru',
  headcount_total_internal: 75,
  industry: 'Industrial sensors',
  product_line_status: 'HUMAN_OR_SIMULATED',
  sources: Object.freeze([
    Object.freeze({ field: 'primary_domain', endpoint: 'POST /company/identify' }),
    Object.freeze({ field: 'year_founded', endpoint: 'POST /company/enrich' }),
    Object.freeze({ field: 'headcount.total', endpoint: 'POST /company/enrich' }),
    Object.freeze({ field: 'locations.headquarters', endpoint: 'POST /company/enrich' }),
    Object.freeze({ field: 'basic_info.description', endpoint: 'POST /company/enrich' }),
  ]),
  confidence: 0.74,
});

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
  suppliers: Object.freeze([supplierOne, supplierTwo]),
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
