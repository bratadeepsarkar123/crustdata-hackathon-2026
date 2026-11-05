'use strict';

// SIMULATED quote builder. No supplier is contacted; every quote is labelled SIMULATED.
const { validateQuote } = require('../contracts/index.cjs');

function buildSimulatedQuote({ displayLabel, unitPrice, leadTimeDays }) {
  const quote = Object.freeze({
    display_label: displayLabel,
    unit_price: unitPrice,
    lead_time_days: leadTimeDays,
    label: 'SIMULATED',
  });
  const check = validateQuote(quote);
  if (!check.valid) {
    throw new Error(`Invalid simulated quote: ${check.errors.join('; ')}`);
  }
  return quote;
}

module.exports = { buildSimulatedQuote };
