'use strict';

// SIMULATED quote builder. No supplier is contacted; every quote is labelled SIMULATED.
const fs = require('node:fs');
const path = require('node:path');
const { validateQuote } = require('../contracts/index.cjs');

const DEFAULT_SIMULATED_QUOTES_PATH = path.resolve(
  __dirname,
  '../../data/simulated/supplier_quotes.json'
);

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

function loadSimulatedQuotes(filePath = DEFAULT_SIMULATED_QUOTES_PATH) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new TypeError('Simulated quotes fixture must be an array');
  }
  return Object.freeze(
    parsed.map((item) => {
      const check = validateQuote(item);
      if (!check.valid) {
        throw new Error(`Invalid quote in fixture: ${check.errors.join('; ')}`);
      }
      return Object.freeze({
        display_label: item.display_label,
        unit_price: item.unit_price,
        lead_time_days: item.lead_time_days,
        label: 'SIMULATED',
      });
    })
  );
}

function rankQuotes(quotes, request) {
  if (!Array.isArray(quotes)) {
    throw new TypeError('quotes must be an array');
  }
  // Filter for display-safe simulated quotes and sort by price ascending then lead time ascending
  const sorted = [...quotes].sort((a, b) => {
    const totalA = a.unit_price * (request ? request.quantity || 1 : 1);
    const totalB = b.unit_price * (request ? request.quantity || 1 : 1);
    if (totalA !== totalB) return totalA - totalB;
    return a.lead_time_days - b.lead_time_days;
  });
  return Object.freeze(
    sorted.map((q) =>
      Object.freeze({
        display_label: q.display_label,
        unit_price: q.unit_price,
        lead_time_days: q.lead_time_days,
        total: request && request.quantity ? q.unit_price * request.quantity : null,
        label: 'SIMULATED',
      })
    )
  );
}

module.exports = {
  buildSimulatedQuote,
  loadSimulatedQuotes,
  rankQuotes,
};
