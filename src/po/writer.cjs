'use strict';

const crypto = require('node:crypto');
const { createIdempotencyStore } = require('../state/idempotency.cjs');
const {
  validateRequest,
  validateSupplier,
  validateQuote,
  validateVendorRecord,
} = require('../contracts/index.cjs');

const REQUIRED_REQUEST_FIELDS = Object.freeze([
  'item', 'quantity', 'budget', 'currency', 'deadline_days', 'region',
]);
const COMPLETED_STATUSES = new Set(['CREATED', 'EXISTS', 'RECOVERED']);

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function canonicalize(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new TypeError('Value must be finite');
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (isRecord(value)) {
    const fields = Object.keys(value).sort().map((key) => {
      if (value[key] === undefined) throw new TypeError('Value cannot contain undefined fields');
      return `${JSON.stringify(key)}:${canonicalize(value[key])}`;
    });
    return `{${fields.join(',')}}`;
  }
  throw new TypeError('Value must be JSON-compatible');
}

function hash(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function toCents(value) {
  if (!Number.isFinite(value) || value <= 0) return null;
  const scaled = value * 100;
  const rounded = Math.round(scaled);
  if (!Number.isSafeInteger(rounded) || Math.abs(scaled - rounded) > 1e-7) return null;
  return rounded;
}

function rejected(...errors) {
  return {
    status: 'REJECTED',
    vendor_status: 'NOT_ATTEMPTED',
    po_status: 'NOT_ATTEMPTED',
    vendor_record: null,
    purchase_order: null,
    errors,
  };
}

function makeRecord({ idempotencyKey, displayLabel, number, total }) {
  return {
    idempotency_key: idempotencyKey,
    display_label: displayLabel,
    po_number: number,
    total,
    status: 'SIMULATED',
    label: 'SIMULATED',
  };
}

function normalizeAttempt(attempt) {
  if (!attempt || !COMPLETED_STATUSES.has(attempt.status) || !attempt.result) return null;
  const validation = validateVendorRecord(attempt.result);
  return validation.valid ? attempt.result : null;
}

function createPurchaseOrderWriter({ stateDirectory, store } = {}) {
  const idempotencyStore = store || createIdempotencyStore({ directory: stateDirectory });
  if (!idempotencyStore || typeof idempotencyStore.executeOnce !== 'function') {
    throw new TypeError('store must provide executeOnce');
  }

  async function writeVendorAndPo({ request, supplier, quote, quoteCurrency, policyDecision } = {}) {
    if (!isRecord(request) || !validateRequest(request).valid || request.missing_fields.length > 0
      || REQUIRED_REQUEST_FIELDS.some((field) => request[field] === null)) {
      return rejected('A complete request is required before creating a vendor record or PO');
    }
    if (!isRecord(supplier) || !validateSupplier(supplier).valid) {
      return rejected('A valid supplier record is required');
    }
    if (!isRecord(quote) || !validateQuote(quote).valid || quote.unit_price <= 0) {
      return rejected('A valid SIMULATED quote with a positive unit price is required');
    }
    if (typeof quoteCurrency !== 'string' || !/^[A-Z]{3}$/.test(quoteCurrency)) {
      return rejected('An explicit three-letter quote currency is required');
    }
    if (quoteCurrency !== request.currency) {
      return rejected('Quote currency must match the request currency');
    }
    if (!isRecord(policyDecision) || policyDecision.label !== 'SIMULATED'
      || policyDecision.approved !== true || policyDecision.display_label !== supplier.display_label
      || typeof policyDecision.reason !== 'string' || policyDecision.reason.trim() === '') {
      return rejected('An explicit approved SIMULATED policy decision for this supplier is required');
    }
    if (supplier.display_label !== quote.display_label) {
      return rejected('Supplier and quote labels must match');
    }
    if (quote.lead_time_days > request.deadline_days) {
      return rejected('The quote delivery time exceeds the request deadline');
    }

    const unitPriceCents = toCents(quote.unit_price);
    const budgetCents = toCents(request.budget);
    const totalCents = toCents(request.quantity * quote.unit_price);
    if (unitPriceCents === null || budgetCents === null || totalCents === null) {
      return rejected('Quantity, unit price, budget, and total must resolve to positive finite amounts with at most two decimal places');
    }
    if (totalCents > budgetCents) return rejected('The computed total exceeds the approved request budget');

    // The request hash is the stable order key for this demo. Distinct buyer
    // orders with identical normalized content therefore share a key; a real
    // workflow should include a stable order/request ID to distinguish them.
    // Private supplier, quote, and decision values are hashed in memory and
    // never put in state or output files.
    let supplierFingerprint;
    let quoteFingerprint;
    let decisionFingerprint;
    try {
      supplierFingerprint = hash(canonicalize(supplier));
      quoteFingerprint = hash(canonicalize(quote));
      decisionFingerprint = hash(canonicalize(policyDecision));
    } catch {
      return rejected('Supplier, quote, and policy decision must be JSON-compatible');
    }
    const requestHash = hash(canonicalize(request));
    const requestKeySuffix = requestHash.slice(0, 32);
    const vendorKey = `vendor:v1:${requestKeySuffix}`;
    const poKey = `po:v1:${requestKeySuffix}`;
    const roundedTotal = totalCents / 100;
    const vendorRecord = makeRecord({
      idempotencyKey: vendorKey,
      displayLabel: supplier.display_label,
      number: `SIM-VENDOR-${requestKeySuffix.slice(0, 12).toUpperCase()}`,
      total: roundedTotal,
    });
    const purchaseOrder = makeRecord({
      idempotencyKey: poKey,
      displayLabel: supplier.display_label,
      number: `SIM-PO-${requestKeySuffix.slice(0, 12).toUpperCase()}`,
      total: roundedTotal,
    });
    const intentFields = {
      kind: 'SIMULATED_VENDOR',
      request_hash: requestHash,
      supplier_fingerprint: supplierFingerprint,
      quote_fingerprint: quoteFingerprint,
      decision_fingerprint: decisionFingerprint,
      display_label: supplier.display_label,
      quantity: request.quantity,
      unit_price_cents: unitPriceCents,
      total_cents: totalCents,
      currency: request.currency,
      lead_time_days: quote.lead_time_days,
    };
    const persistRecord = (record) => async ({ persistResult }) => {
      await persistResult(record);
      return record;
    };

    const vendorAttempt = await idempotencyStore.executeOnce({
      idempotencyKey: vendorKey,
      payload: intentFields,
      write: persistRecord(vendorRecord),
    });
    const persistedVendor = normalizeAttempt(vendorAttempt);
    if (!persistedVendor) {
      return {
        status: vendorAttempt.status,
        vendor_status: vendorAttempt.status,
        po_status: 'NOT_ATTEMPTED',
        vendor_record: null,
        purchase_order: null,
        errors: [],
      };
    }

    const poAttempt = await idempotencyStore.executeOnce({
      idempotencyKey: poKey,
      payload: { ...intentFields, kind: 'SIMULATED_PO' },
      write: persistRecord(purchaseOrder),
    });
    const persistedPo = normalizeAttempt(poAttempt);
    return {
      status: poAttempt.status,
      vendor_status: vendorAttempt.status,
      po_status: poAttempt.status,
      vendor_record: persistedVendor,
      purchase_order: persistedPo,
      errors: [],
    };
  }

  return Object.freeze({ writeVendorAndPo });
}

module.exports = Object.freeze({ createPurchaseOrderWriter });
