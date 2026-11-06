'use strict';

const { validateQuote } = require('../contracts/index.cjs');

/**
 * Task 2: One-item quote builder for Person 3.
 * Item: "neodymium speaker magnet, 3 mm thick"
 * Buyer: US buyer, quantity 1,000 pcs (simulated).
 * Display label: "Supplier 1" only.
 * Never put a real company name or domain in the repo.
 * Conforms strictly to validateQuote (display_label, unit_price, lead_time_days, label: 'SIMULATED').
 */

const ONE_ITEM_REQUEST = Object.freeze({
  item: 'neodymium speaker magnet, 3 mm thick',
  quantity: 1000,
  buyer_region: 'US',
  currency: 'USD',
  label: 'SIMULATED',
});

const ONE_ITEM_QUOTE = Object.freeze({
  display_label: 'Supplier 1',
  unit_price: 1.25,
  lead_time_days: 7,
  label: 'SIMULATED',
});

// Verify validity at load time
const initialCheck = validateQuote(ONE_ITEM_QUOTE);
if (!initialCheck.valid) {
  throw new Error(`Invalid ONE_ITEM_QUOTE: ${initialCheck.errors.join('; ')}`);
}

function buildOneItemQuote(overrides = {}) {
  const quote = Object.freeze({
    display_label: overrides.displayLabel || overrides.display_label || ONE_ITEM_QUOTE.display_label,
    unit_price: overrides.unitPrice !== undefined ? overrides.unitPrice : (overrides.unit_price !== undefined ? overrides.unit_price : ONE_ITEM_QUOTE.unit_price),
    lead_time_days: overrides.leadTimeDays !== undefined ? overrides.leadTimeDays : (overrides.lead_time_days !== undefined ? overrides.lead_time_days : ONE_ITEM_QUOTE.lead_time_days),
    label: 'SIMULATED',
  });
  const check = validateQuote(quote);
  if (!check.valid) {
    throw new Error(`Invalid simulated quote: ${check.errors.join('; ')}`);
  }
  return quote;
}

module.exports = Object.freeze({
  ONE_ITEM_REQUEST,
  ONE_ITEM_QUOTE,
  buildOneItemQuote,
});
