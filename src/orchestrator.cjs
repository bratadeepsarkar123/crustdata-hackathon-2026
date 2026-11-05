'use strict';

// This harness intentionally uses the intake parser and simulated PO writer
// only. Discovery, verification, dedupe, WhatsApp, quotes, and policy are
// represented by a prerecorded SIMULATED fixture; no network modules are used.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { isDeepStrictEqual } = require('node:util');
const { parseRequest } = require('./intake/request-reader.cjs');
const { createPurchaseOrderWriter } = require('./po/writer.cjs');
const {
  validateQuote,
  validateRequest,
  validateSupplier,
  validateVendorRecord,
  toSupplierDisplay,
} = require('./contracts/index.cjs');
const { sampleRequests } = require('../samples/requests.cjs');
const fullFlowFixture = require('../samples/full-flow.cjs');

const SIMULATED_SOURCE = 'SIMULATED fixture; no live Crustdata call';
const FLOW_FIXTURE_KEYS = Object.freeze([
  'label', 'request_text', 'request', 'suppliers', 'quotes', 'quote_currency_by_label', 'policy_decision', 'chosen_supplier_label',
]);
const POLICY_DECISION_KEYS = Object.freeze(['label', 'approved', 'display_label', 'reason']);
const SCREEN_RECORD_KEYS = Object.freeze([
  'idempotency_key', 'display_label', 'po_number', 'total', 'status', 'label',
]);

class OfflineFlowError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'OfflineFlowError';
    this.code = code;
  }
}

function reject(code, message) {
  throw new OfflineFlowError(code, message);
}

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function hasExactKeys(value, keys) {
  return isRecord(value)
    && Object.keys(value).length === keys.length
    && keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

function isWithin(parent, candidate) {
  const relative = path.relative(parent, candidate);
  return relative !== '' && relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

function safeStateDirectory(requestedPath) {
  const tempRoot = fs.realpathSync(os.tmpdir());
  const defaultPath = path.join(tempRoot, 'contextcon-supplier-agent', 'offline-fixture-state');
  const resolved = path.resolve(requestedPath || defaultPath);
  if (!isWithin(tempRoot, resolved)) {
    reject('UNSAFE_STATE_DIRECTORY', 'State directory must be a child of the operating-system temporary directory.');
  }

  // Check the nearest existing ancestor too, so a symlink cannot redirect
  // state out of the temporary directory.
  let existingAncestor = resolved;
  while (!fs.existsSync(existingAncestor)) {
    const parent = path.dirname(existingAncestor);
    if (parent === existingAncestor) break;
    existingAncestor = parent;
  }
  const realAncestor = fs.realpathSync(existingAncestor);
  if (realAncestor !== tempRoot && !isWithin(tempRoot, realAncestor)) {
    reject('UNSAFE_STATE_DIRECTORY', 'State directory resolves outside the operating-system temporary directory.');
  }
  return resolved;
}

function validateFixture(fixture, requestText, parsedRequest, expectedRequest) {
  if (!hasExactKeys(fixture, FLOW_FIXTURE_KEYS)) reject('UNSAFE_FIXTURE', 'Full-flow fixture has an unexpected shape.');
  if (fixture.label !== 'SIMULATED') reject('UNSAFE_FIXTURE', 'Full-flow fixture must be labelled SIMULATED.');
  if (fixture.request_text !== requestText) reject('FIXTURE_REQUEST_MISMATCH', 'Fixture text does not match the selected sample request.');
  if (!validateRequest(fixture.request).valid) reject('UNSAFE_FIXTURE', 'Fixture request does not match the shared request contract.');
  if (!isDeepStrictEqual(fixture.request, expectedRequest)) reject('FIXTURE_REQUEST_MISMATCH', 'Fixture request does not match the expected parsed sample.');
  if (!isDeepStrictEqual(parsedRequest, expectedRequest)) reject('PARSED_REQUEST_MISMATCH', 'Parsed request does not exactly match the sample expectation.');

  if (!Array.isArray(fixture.suppliers) || fixture.suppliers.length === 0) {
    reject('UNSAFE_FIXTURE', 'Fixture must contain at least one supplier candidate.');
  }
  const supplierLabels = new Set();
  for (const supplier of fixture.suppliers) {
    if (!validateSupplier(supplier).valid) reject('UNSAFE_FIXTURE', 'Fixture contains an invalid supplier or citation.');
    if (supplierLabels.has(supplier.display_label)) reject('UNSAFE_FIXTURE', 'Fixture contains duplicate supplier labels.');
    supplierLabels.add(supplier.display_label);
  }

  if (!Array.isArray(fixture.quotes) || fixture.quotes.length === 0) {
    reject('UNSAFE_FIXTURE', 'Fixture must contain at least one simulated quote.');
  }
  const quoteLabels = new Set();
  for (const quote of fixture.quotes) {
    if (!validateQuote(quote).valid || !supplierLabels.has(quote.display_label)) {
      reject('UNSAFE_FIXTURE', 'Fixture contains an invalid or unmatched simulated quote.');
    }
    if (quoteLabels.has(quote.display_label)) reject('UNSAFE_FIXTURE', 'Fixture contains duplicate quote labels.');
    quoteLabels.add(quote.display_label);
  }
  if (!hasExactKeys(fixture.quote_currency_by_label, [...quoteLabels])) {
    reject('UNSAFE_FIXTURE', 'Fixture must provide exactly one quote currency for each simulated quote.');
  }
  for (const label of quoteLabels) {
    if (typeof fixture.quote_currency_by_label[label] !== 'string'
      || !/^[A-Z]{3}$/.test(fixture.quote_currency_by_label[label])) {
      reject('UNSAFE_FIXTURE', 'Fixture quote currencies must be three-letter uppercase codes.');
    }
  }

  const decision = fixture.policy_decision;
  if (!hasExactKeys(decision, POLICY_DECISION_KEYS)
    || decision.label !== 'SIMULATED'
    || typeof decision.approved !== 'boolean'
    || decision.display_label !== fixture.chosen_supplier_label
    || !supplierLabels.has(decision.display_label)
    || typeof decision.reason !== 'string') {
    reject('UNSAFE_FIXTURE', 'Fixture policy decision has an invalid shape.');
  }
  if (!decision.approved) reject('POLICY_NOT_APPROVED', 'The simulated policy decision is not approved; no vendor or PO was written.');

  const chosenQuote = fixture.quotes.find((quote) => quote.display_label === decision.display_label);
  if (!chosenQuote) reject('UNSAFE_FIXTURE', 'Approved supplier has no matching simulated quote.');
  const chosenQuoteCurrency = fixture.quote_currency_by_label[chosenQuote.display_label];
  if (chosenQuoteCurrency !== parsedRequest.currency) {
    reject('QUOTE_CURRENCY_MISMATCH', 'The chosen quote currency does not match the sample request currency; no PO was written.');
  }
  const total = chosenQuote.unit_price * parsedRequest.quantity;
  if (!Number.isFinite(total) || total > parsedRequest.budget || chosenQuote.lead_time_days > parsedRequest.deadline_days) {
    reject('POLICY_CONSTRAINT_FAILED', 'The chosen simulated quote exceeds the sample request constraints; no PO was written.');
  }
  return { chosenQuote, chosenQuoteCurrency };
}

function citeSimulatedFixture(supplier) {
  const projection = toSupplierDisplay(supplier);
  return {
    label: 'SIMULATED',
    display_label: projection.display_label,
    sources: projection.sources.map(({ field, endpoint }) => ({
      field,
      endpoint,
      source: SIMULATED_SOURCE,
    })),
  };
}

function screenRecord(record, name) {
  if (!validateVendorRecord(record).valid) reject('PO_WRITE_INVALID', `The simulated writer returned an invalid ${name} record.`);
  return Object.fromEntries(SCREEN_RECORD_KEYS.map((key) => [key, record[key]]));
}

function summarizeWriteStatus(value) {
  const status = typeof value === 'string' ? value.toLowerCase() : '';
  const allowed = new Set(['created', 'exists', 'recovered']);
  return allowed.has(status) ? status.toUpperCase() : 'COMPLETED';
}

/**
 * Run the prerecorded offline supplier flow. Only exact sample request text
 * is accepted. Stages 2–6 are fixture data; stage 7 uses the local,
 * idempotent simulated PO writer. This function never makes network calls.
 */
async function runOfflineFixture({
  requestText = fullFlowFixture.request_text,
  fixture = fullFlowFixture,
  stateDirectory,
} = {}) {
  const matchingSample = sampleRequests.find((sample) => sample.text === requestText);
  if (!matchingSample) reject('REQUEST_NOT_IN_FIXTURES', 'Only exact SIMULATED sample request text is accepted.');

  let parsedRequest;
  try {
    parsedRequest = parseRequest(requestText);
  } catch {
    reject('REQUEST_PARSE_FAILED', 'The SIMULATED sample request could not be parsed.');
  }
  if (!validateRequest(parsedRequest).valid) reject('PARSED_REQUEST_INVALID', 'The parser returned an invalid request shape.');
  if (!isDeepStrictEqual(parsedRequest, matchingSample.request)) {
    reject('PARSED_REQUEST_MISMATCH', 'Parsed request does not exactly match the expected sample.');
  }
  if (parsedRequest.missing_fields.length > 0) {
    reject('MISSING_REQUEST_FIELDS', 'The sample request has unresolved fields; no vendor or PO was written.');
  }

  const { chosenQuote, chosenQuoteCurrency } = validateFixture(fixture, requestText, parsedRequest, matchingSample.request);
  // Default state is a folder named after this exact fixture version, so a changed
  // fixture never collides with records written for an earlier one, and nothing is
  // ever deleted on conflict.
  const fixtureVersion = require('node:crypto')
    .createHash('sha256')
    .update(JSON.stringify([fixture.chosen_supplier_label, chosenQuote, chosenQuoteCurrency, fixture.policy_decision, parsedRequest]))
    .digest('hex')
    .slice(0, 16);
  const defaultStateDirectory = path.join(os.tmpdir(), 'contextcon-supplier-agent', 'offline-fixture-state', fixtureVersion);
  const safeStatePath = safeStateDirectory(stateDirectory || defaultStateDirectory);
  const writer = createPurchaseOrderWriter({ stateDirectory: safeStatePath });
  let writeResult;
  try {
    writeResult = await writer.writeVendorAndPo({
      request: parsedRequest,
      supplier: fixture.suppliers.find((supplier) => supplier.display_label === fixture.chosen_supplier_label),
      quote: chosenQuote,
      quoteCurrency: chosenQuoteCurrency,
      policyDecision: fixture.policy_decision,
    });
  } catch {
    reject('PO_WRITE_FAILED', 'The simulated vendor/PO write failed. No writer error details were displayed.');
  }

  if (!isRecord(writeResult) || !writeResult.vendor_record || !writeResult.purchase_order) {
    reject('PO_WRITE_FAILED', 'The simulated writer did not return both vendor and PO records.');
  }
  const vendorRecord = screenRecord(writeResult.vendor_record, 'vendor');
  const purchaseOrder = screenRecord(writeResult.purchase_order, 'purchase order');
  if (vendorRecord.idempotency_key === purchaseOrder.idempotency_key) {
    reject('PO_WRITE_INVALID', 'Vendor and PO writes must use separate idempotency keys.');
  }
  if (vendorRecord.display_label !== fixture.chosen_supplier_label
    || purchaseOrder.display_label !== fixture.chosen_supplier_label) {
    reject('PO_WRITE_INVALID', 'Writer output does not match the chosen neutral supplier label.');
  }

  return {
    label: 'SIMULATED',
    mode: 'OFFLINE_FIXTURE_ONLY',
    request: parsedRequest,
    request_label: 'SIMULATED',
    steps: [
      { step: 1, name: 'Parse request', status: 'PARSED', label: 'SIMULATED', source: 'Sample request fixture; parser executed locally' },
      { step: 2, name: 'Find candidate suppliers', status: 'FIXTURE', label: 'SIMULATED', source: SIMULATED_SOURCE },
      { step: 3, name: 'Verify companies', status: 'FIXTURE', label: 'SIMULATED', source: SIMULATED_SOURCE },
      { step: 4, name: 'Dedupe suppliers', status: 'FIXTURE', label: 'SIMULATED', source: SIMULATED_SOURCE },
      { step: '5a', name: 'Supplier contact request', status: 'NOT_SENT', label: 'SIMULATED', source: 'No message was sent; prerecorded fixture only' },
      { step: '5b', name: 'Supplier reply and quote', status: 'FIXTURE', label: 'SIMULATED', source: SIMULATED_SOURCE },
      { step: 6, name: 'Policy comparison', status: 'STUB_DECISION', label: 'SIMULATED', source: SIMULATED_SOURCE },
      {
        step: 7,
        name: 'Vendor record and purchase order',
        status: 'WRITTEN',
        label: 'SIMULATED',
        vendor_status: summarizeWriteStatus(writeResult.vendor_status),
        po_status: summarizeWriteStatus(writeResult.po_status),
        source: 'Local filesystem writer; idempotency keys recorded before each write',
      },
    ],
    suppliers: fixture.suppliers.map(citeSimulatedFixture),
    quotes: fixture.quotes.map((quote) => ({
      label: 'SIMULATED',
      currency: fixture.quote_currency_by_label[quote.display_label],
      source: SIMULATED_SOURCE,
      quote: { ...quote },
    })),
    policy_decision: {
      label: 'SIMULATED',
      approved: fixture.policy_decision.approved,
      display_label: fixture.policy_decision.display_label,
      source: SIMULATED_SOURCE,
    },
    vendor_record: {
      label: 'SIMULATED',
      currency: parsedRequest.currency,
      source: 'SIMULATED local writer',
      record: vendorRecord,
    },
    purchase_order: {
      label: 'SIMULATED',
      currency: parsedRequest.currency,
      source: 'SIMULATED local writer',
      record: purchaseOrder,
    },
  };
}

async function main(argv = process.argv.slice(2)) {
  if (argv.length > 1) reject('USAGE', 'Usage: node src/orchestrator.cjs [temporary-state-directory]');
  const output = await runOfflineFixture({ stateDirectory: argv[0] });
  process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    const message = error instanceof OfflineFlowError ? error.message : 'Offline fixture run failed.';
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  });
}

module.exports = Object.freeze({
  OfflineFlowError,
  runOfflineFixture,
  safeStateDirectory,
});
