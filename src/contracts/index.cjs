'use strict';

const REQUEST_KEYS = Object.freeze([
  'item', 'quantity', 'budget', 'currency', 'deadline_days', 'region', 'missing_fields',
]);
const REQUEST_VALUE_FIELDS = Object.freeze([
  'item', 'quantity', 'budget', 'currency', 'deadline_days', 'region',
]);
const SUPPLIER_KEYS = Object.freeze([
  'display_label', 'name_internal', 'primary_domain', 'year_founded',
  'headquarters_internal', 'headcount_total_internal', 'industry',
  'product_line_status', 'sources', 'confidence',
]);
const QUOTE_KEYS = Object.freeze(['display_label', 'unit_price', 'lead_time_days', 'label']);
const VENDOR_RECORD_KEYS = Object.freeze([
  'idempotency_key', 'display_label', 'po_number', 'total', 'status', 'label',
]);
const SAFE_CITATION_ENDPOINTS = Object.freeze({
  primary_domain: 'POST /company/identify',
  year_founded: 'POST /company/enrich',
  'headcount.total': 'POST /company/enrich',
  'locations.headquarters': 'POST /company/enrich',
  'basic_info.description': 'POST /company/enrich',
});

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function checkExactKeys(value, keys, shapeName, errors) {
  if (!isRecord(value)) {
    errors.push(`${shapeName} must be an object`);
    return false;
  }
  for (const key of keys) {
    if (!Object.prototype.hasOwnProperty.call(value, key)) errors.push(`${shapeName}.${key} is required`);
  }
  for (const key of Object.keys(value)) {
    if (!keys.includes(key)) errors.push(`${shapeName}.${key} is not allowed`);
  }
  return true;
}

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function result(errors) {
  return { valid: errors.length === 0, errors };
}

/** Section 6 Request validator. A null value must be named in missing_fields. */
function validateRequest(request) {
  const errors = [];
  if (!checkExactKeys(request, REQUEST_KEYS, 'request', errors)) return result(errors);
  if (!Array.isArray(request.missing_fields)) {
    errors.push('request.missing_fields must be an array');
    return result(errors);
  }

  const validMissingFields = new Set(REQUEST_VALUE_FIELDS);
  const seenMissingFields = new Set();
  for (const field of request.missing_fields) {
    if (typeof field !== 'string' || !validMissingFields.has(field)) {
      errors.push('request.missing_fields must contain only request field names');
      continue;
    }
    if (seenMissingFields.has(field)) errors.push(`request.missing_fields contains duplicate ${field}`);
    seenMissingFields.add(field);
  }

  const nullable = (field, isValid, description) => {
    const value = request[field];
    const markedMissing = seenMissingFields.has(field);
    if (value === null) {
      if (!markedMissing) errors.push(`request.${field} is null but is not listed in missing_fields`);
    } else {
      if (markedMissing) errors.push(`request.${field} is present but is listed in missing_fields`);
      if (!isValid(value)) errors.push(`request.${field} ${description}`);
    }
  };

  nullable('item', isNonEmptyString, 'must be a non-empty string or null');
  nullable('quantity', (value) => isFiniteNumber(value) && value > 0, 'must be a positive number or null');
  nullable('budget', (value) => isFiniteNumber(value) && value >= 0, 'must be a non-negative number or null');
  nullable('currency', (value) => typeof value === 'string' && /^[A-Z]{3}$/.test(value), 'must be a 3-letter uppercase code or null');
  nullable('deadline_days', (value) => Number.isInteger(value) && value > 0, 'must be a positive integer or null');
  nullable('region', isNonEmptyString, 'must be a non-empty string or null');
  return result(errors);
}

/** Section 6 candidate/verified-supplier validator. */
function validateSupplier(supplier) {
  const errors = [];
  if (!checkExactKeys(supplier, SUPPLIER_KEYS, 'supplier', errors)) return result(errors);
  if (!/^Supplier [1-9]\d*$/.test(supplier.display_label)) errors.push('supplier.display_label must be a neutral label such as Supplier 1');
  if (supplier.name_internal !== null && !isNonEmptyString(supplier.name_internal)) errors.push('supplier.name_internal must be a non-empty string or null');
  if (supplier.primary_domain !== null && !isNonEmptyString(supplier.primary_domain)) errors.push('supplier.primary_domain must be a non-empty string or null');
  if (supplier.year_founded !== null && (!Number.isInteger(supplier.year_founded) || supplier.year_founded < 1)) errors.push('supplier.year_founded must be a positive integer or null');
  if (supplier.headquarters_internal !== null && !isNonEmptyString(supplier.headquarters_internal)) errors.push('supplier.headquarters_internal must be a non-empty string or null');
  if (supplier.headcount_total_internal !== null && (!Number.isInteger(supplier.headcount_total_internal) || supplier.headcount_total_internal < 0)) errors.push('supplier.headcount_total_internal must be a non-negative integer or null');
  if (supplier.industry !== null && !isNonEmptyString(supplier.industry)) errors.push('supplier.industry must be a non-empty string or null');
  if (!['CONFIRMED', 'HUMAN_OR_SIMULATED'].includes(supplier.product_line_status)) errors.push('supplier.product_line_status must be CONFIRMED or HUMAN_OR_SIMULATED');
  if (!Array.isArray(supplier.sources)) {
    errors.push('supplier.sources must be an array');
  } else {
    supplier.sources.forEach((source, index) => {
      const path = `supplier.sources[${index}]`;
      if (!checkExactKeys(source, ['field', 'endpoint'], path, errors)) return;
      if (!Object.prototype.hasOwnProperty.call(SAFE_CITATION_ENDPOINTS, source.field)) {
        errors.push(`${path}.field is not an allowlisted citation field`);
      } else if (source.endpoint !== SAFE_CITATION_ENDPOINTS[source.field]) {
        errors.push(`${path}.endpoint must be the allowlisted endpoint for ${source.field}`);
      }
    });
  }
  if (supplier.confidence !== null && (!isFiniteNumber(supplier.confidence) || supplier.confidence < 0 || supplier.confidence > 1)) errors.push('supplier.confidence must be a number from 0 through 1 or null');
  return result(errors);
}

/** Section 6 simulated quote validator. */
function validateQuote(quote) {
  const errors = [];
  if (!checkExactKeys(quote, QUOTE_KEYS, 'quote', errors)) return result(errors);
  if (!/^Supplier [1-9]\d*$/.test(quote.display_label)) errors.push('quote.display_label must be a neutral supplier label');
  if (!isFiniteNumber(quote.unit_price) || quote.unit_price < 0) errors.push('quote.unit_price must be a non-negative number');
  if (!Number.isInteger(quote.lead_time_days) || quote.lead_time_days < 0) errors.push('quote.lead_time_days must be a non-negative integer');
  if (quote.label !== 'SIMULATED') errors.push('quote.label must be SIMULATED');
  return result(errors);
}

/** Section 6 simulated vendor-record and PO validator. */
function validateVendorRecord(record) {
  const errors = [];
  if (!checkExactKeys(record, VENDOR_RECORD_KEYS, 'vendor_record_or_po', errors)) return result(errors);
  if (!isNonEmptyString(record.idempotency_key)) errors.push('vendor_record_or_po.idempotency_key must be a non-empty string');
  if (!/^Supplier [1-9]\d*$/.test(record.display_label)) errors.push('vendor_record_or_po.display_label must be a neutral supplier label');
  if (!isNonEmptyString(record.po_number)) errors.push('vendor_record_or_po.po_number must be a non-empty string');
  if (!isFiniteNumber(record.total) || record.total < 0) errors.push('vendor_record_or_po.total must be a non-negative number');
  if (!isNonEmptyString(record.status)) errors.push('vendor_record_or_po.status must be a non-empty string');
  if (record.label !== 'SIMULATED') errors.push('vendor_record_or_po.label must be SIMULATED');
  return result(errors);
}

/** Only a neutral label and field/endpoint citations reach screen output. */
function toSupplierDisplay(supplier) {
  const validation = validateSupplier(supplier);
  if (!validation.valid) throw new TypeError(`Invalid supplier cannot be projected: ${validation.errors.join('; ')}`);
  return {
    display_label: supplier.display_label,
    sources: supplier.sources.map(({ field }) => ({
      field,
      endpoint: SAFE_CITATION_ENDPOINTS[field],
    })),
  };
}

module.exports = Object.freeze({
  validateRequest,
  validateSupplier,
  validateQuote,
  validateVendorRecord,
  toSupplierDisplay,
});
