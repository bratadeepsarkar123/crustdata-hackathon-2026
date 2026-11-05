'use strict';

const { validateRequest } = require('../contracts/index.cjs');

const VALUE_FIELDS = Object.freeze([
  'item',
  'quantity',
  'budget',
  'currency',
  'deadline_days',
  'region',
]);

const CURRENCY_CODES = new Set([
  'AED', 'AUD', 'CAD', 'CHF', 'CNY', 'EUR', 'GBP', 'HKD', 'INR', 'JPY',
  'NZD', 'SGD', 'USD',
]);

const AMOUNT_SCALES = Object.freeze({
  k: 1_000,
  thousand: 1_000,
  lakh: 100_000,
  lakhs: 100_000,
  lac: 100_000,
  lacs: 100_000,
  million: 1_000_000,
  crore: 10_000_000,
  crores: 10_000_000,
  billion: 1_000_000_000,
});

function numericValue(raw) {
  const value = Number(raw.replace(/,/g, ''));
  return Number.isFinite(value) ? value : null;
}

function parseItemAndQuantity(text) {
  const ambiguousQuantity = text.match(
    /\b(?:need|source|procure|purchase|order)\s+\d[\d,]*(?:\.\d+)?\s*(?:-|–|—|to\b|or\b|and\b)\s*\d[\d,]*(?:\.\d+)?/i,
  );
  if (ambiguousQuantity) return { item: null, quantity: null };

  const match = text.match(
    /\b(?:need|source|procure|purchase|order)\s+(\d[\d,]*(?:\.\d+)?)\s+(.+?)(?=\s+(?:delivered|delivery|for|to)\b|[;,.!?]|$)/i,
  );
  if (!match) return { item: null, quantity: null };

  const quantity = numericValue(match[1]);
  const item = match[2].trim().replace(/\s+/g, ' ');
  if (quantity === null || quantity <= 0 || item.length === 0) {
    return { item: null, quantity: null };
  }
  return { item, quantity };
}

function parseRegion(text) {
  const candidates = [];
  let ambiguous = false;
  const add = (value, endIndex) => {
    const region = value.trim().replace(/\s+/g, ' ').replace(/[,.!?;]+$/, '');
    if (/\b(?:and|or)\b|[,/]/i.test(region)) {
      ambiguous = true;
      return;
    }
    const trailingText = text.slice(endIndex);
    if (/^\s*(?:,|\/|\b(?:and|or)\b)\s+[\p{Lu}]/u.test(trailingText)) ambiguous = true;
    if (region && !candidates.includes(region)) candidates.push(region);
  };

  const deliveryMatch = text.match(
    /\b(?:delivered|deliver|shipped|ship)\s+to\s+([\p{L}][\p{L}\p{M}.'-]*(?:\s+[\p{L}][\p{L}\p{M}.'-]*){0,2})(?=\s+(?:within|inside|in\s+\d|by\s+\d)\b|[,;.?!]|$)/iu,
  );
  if (deliveryMatch) add(deliveryMatch[1], deliveryMatch.index + deliveryMatch[0].length);

  const plantMatch = text.match(
    /\bfor\s+our\s+([\p{Lu}][\p{L}\p{M}.'-]*(?:\s+[\p{Lu}][\p{L}\p{M}.'-]*){0,2})\s+plant\b/u,
  );
  if (plantMatch) add(plantMatch[1], plantMatch.index + plantMatch[0].length);

  const explicitPlaceMatch = text.match(
    /\bfor\s+([\p{Lu}][\p{L}\p{M}.'-]*(?:\s+[\p{Lu}][\p{L}\p{M}.'-]*){0,2})(?=\s+(?:within|inside|in\s+\d|by\s+\d)\b|[,;.?!]|$)/u,
  );
  if (explicitPlaceMatch) add(explicitPlaceMatch[1], explicitPlaceMatch.index + explicitPlaceMatch[0].length);

  const labeledRegionMatch = text.match(
    /\bregion\s*[:=]\s*([^,;.?!]+?)(?=\s+(?:within|inside|by)\b|[,;.?!]|$)/i,
  );
  if (labeledRegionMatch) add(labeledRegionMatch[1], labeledRegionMatch.index + labeledRegionMatch[0].length);

  return !ambiguous && candidates.length === 1 ? candidates[0] : null;
}

function parseDeadlineDays(text) {
  const values = [];
  const durationPattern = /\b(?:within|inside|in)\s+(\d[\d,]*(?:\.\d+)?)\s*(days?|weeks?)\b/gi;
  for (const match of text.matchAll(durationPattern)) {
    const afterMatch = text.slice(match.index + match[0].length);
    if (/^\s*(?:-|–|—|to\b|or\b)\s*\d/i.test(afterMatch)) return null;

    const amount = numericValue(match[1]);
    const days = /^weeks?$/i.test(match[2]) ? amount * 7 : amount;
    if (days !== null && Number.isInteger(days) && days > 0 && !values.includes(days)) {
      values.push(days);
    } else if (days !== null && (!Number.isInteger(days) || days <= 0)) {
      return null;
    }
  }
  return values.length === 1 ? values[0] : null;
}

function findCurrencyCodes(text) {
  const codes = [];
  const codePattern = /\b(AED|AUD|CAD|CHF|CNY|EUR|GBP|HKD|INR|JPY|NZD|SGD|USD)\b/gi;
  for (const match of text.matchAll(codePattern)) {
    const code = match[1].toUpperCase();
    if (!codes.includes(code)) codes.push(code);
  }
  return codes;
}

function parseCurrency(text, codes) {
  const symbolTypes = [];
  if (text.includes('₹')) symbolTypes.push('INR');
  if (text.includes('€')) symbolTypes.push('EUR');
  if (text.includes('£')) symbolTypes.push('GBP');
  if (text.includes('$')) symbolTypes.push('DOLLAR');
  if (text.includes('¥')) symbolTypes.push('YEN_OR_YUAN');

  const uniqueSymbols = [...new Set(symbolTypes)];
  if (codes.length > 1 || uniqueSymbols.length > 1) return null;
  if (codes.length === 1) {
    const code = codes[0];
    const compatible = uniqueSymbols.length === 0
      || (uniqueSymbols[0] === code)
      || (uniqueSymbols[0] === 'DOLLAR' && ['USD', 'CAD', 'AUD', 'NZD', 'SGD', 'HKD'].includes(code))
      || (uniqueSymbols[0] === 'YEN_OR_YUAN' && ['JPY', 'CNY'].includes(code));
    return compatible ? code : null;
  }

  if (uniqueSymbols.length !== 1) return null;
  return ['INR', 'EUR', 'GBP'].includes(uniqueSymbols[0]) ? uniqueSymbols[0] : null;
}

function isNearBudgetLanguage(text, start, end) {
  const window = text.slice(Math.max(0, start - 55), Math.min(text.length, end + 35));
  return /\b(?:budget|total\s+(?:spend|budget|cost)|maximum|max|below|under|up\s+to|all[- ]in)\b/i.test(window);
}

function parseAmount(rawNumber, rawScale) {
  const base = numericValue(rawNumber);
  if (base === null || base < 0) return null;
  const scale = rawScale ? AMOUNT_SCALES[rawScale.toLowerCase()] : 1;
  if (!scale) return null;
  const amount = base * scale;
  return Number.isFinite(amount) ? amount : null;
}

function findBudgetAmounts(text) {
  const amounts = [];
  const add = (start, end, rawNumber, rawScale) => {
    if (!isNearBudgetLanguage(text, start, end)) return;
    const amount = parseAmount(rawNumber, rawScale);
    if (amount === null) return;
    // Prefix, suffix, and scaled-amount scans can all find the same token.
    // Treat overlapping spans as one amount while keeping distinct amounts
    // (which may form a range) separate.
    if (!amounts.some((entry) => start < entry.end && end > entry.start)) {
      amounts.push({ start, end, amount });
    }
  };

  const currencyAmountPattern =
    /(?:₹|[$€£¥]|\b(?:AED|AUD|CAD|CHF|CNY|EUR|GBP|HKD|INR|JPY|NZD|SGD|USD)\b)\s*(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|crore|crores|thousand|million|billion|k)?/gi;
  for (const match of text.matchAll(currencyAmountPattern)) {
    add(match.index, match.index + match[0].length, match[1], match[2]);
  }

  const suffixCodePattern =
    /(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|crore|crores|thousand|million|billion|k)?\s*\b(AED|AUD|CAD|CHF|CNY|EUR|GBP|HKD|INR|JPY|NZD|SGD|USD)\b/gi;
  for (const match of text.matchAll(suffixCodePattern)) {
    add(match.index, match.index + match[0].length, match[1], match[2]);
  }

  const scaledAmountPattern =
    /(?<![\p{L}\d.])(\d[\d,]*(?:\.\d+)?)\s*(lakh|lakhs|lac|lacs|crore|crores|thousand|million|billion|k)\b/giu;
  for (const match of text.matchAll(scaledAmountPattern)) {
    add(match.index, match.index + match[0].length, match[1], match[2]);
  }

  const bareBudgetPattern =
    /\b(?:budget|total\s+(?:spend|budget|cost)|maximum|max|below|under|up\s+to)\b[^\d]{0,24}(\d[\d,]*(?:\.\d+)?)(?!\s*(?:days?|weeks?)\b)/gi;
  for (const match of text.matchAll(bareBudgetPattern)) {
    const offset = match[0].lastIndexOf(match[1]);
    add(match.index + offset, match.index + offset + match[1].length, match[1], null);
  }

  return amounts.sort((a, b) => a.start - b.start);
}

function hasApproximationOrRange(text, amount) {
  const before = text.slice(Math.max(0, amount.start - 24), amount.start);
  const after = text.slice(amount.end, Math.min(text.length, amount.end + 32));
  if (/\b(?:about|around|roughly|approximately|approx\.?|at\s+least|more\s+than|between)\b|~\s*$/i.test(before)) {
    return true;
  }
  if (/^\s*(?:-|–|—|to\b|or\b)/i.test(after)) return true;
  if (/^\s*and\s+(?:(?:₹|[$€£¥]|\b(?:AED|AUD|CAD|CHF|CNY|EUR|GBP|HKD|INR|JPY|NZD|SGD|USD)\b)\s*)?\d[\d,]*(?:\.\d+)?(?!\s*(?:days?|weeks?)\b)/i.test(after)) return true;
  return /^\s*(?:per\s+(?:unit|item|piece|sensor|probe|transmitter)|each)\b/i.test(after);
}

function parseBudget(text) {
  const codes = findCurrencyCodes(text);
  const currency = parseCurrency(text, codes);
  const amounts = findBudgetAmounts(text);
  if (amounts.length !== 1 || hasApproximationOrRange(text, amounts[0])) {
    return { budget: null, currency };
  }

  // A numeric ceiling without a currency is not a usable procurement budget.
  if (!currency) return { budget: null, currency: null };
  return { budget: amounts[0].amount, currency };
}

function parseRequest(text) {
  if (typeof text !== 'string') throw new TypeError('Request text must be a string');

  const normalized = text.normalize('NFKC').replace(/\s+/g, ' ').trim();
  const { item, quantity } = parseItemAndQuantity(normalized);
  const { budget, currency } = parseBudget(normalized);
  const request = {
    item,
    quantity,
    budget,
    currency,
    deadline_days: parseDeadlineDays(normalized),
    region: parseRegion(normalized),
    missing_fields: [],
  };
  request.missing_fields = VALUE_FIELDS.filter((field) => request[field] === null);

  const validation = validateRequest(request);
  if (!validation.valid) {
    throw new Error(`Request parser produced an invalid contract: ${validation.errors.join('; ')}`);
  }
  return request;
}

module.exports = Object.freeze({ parseRequest });
