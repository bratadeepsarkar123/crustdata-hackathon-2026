'use strict';

const candidates = require('./candidates.json');

/**
 * Ranked, verified, and deduped supplier candidates from Discovery (Steps 2 to 4).
 * Generated from src/discovery/fixtures.py via run_discovery_pipeline.
 *
 * Each record satisfies validateSupplier() from src/contracts/index.cjs:
 * - display_label ("Supplier 1", ...)
 * - name_internal
 * - primary_domain
 * - year_founded
 * - headquarters_internal
 * - headcount_total_internal
 * - industry
 * - product_line_status ("CONFIRMED" or "HUMAN_OR_SIMULATED")
 * - sources (array of { field, endpoint })
 * - confidence
 */
const discoveryCandidates = Object.freeze(
  candidates.map((candidate) =>
    Object.freeze({
      ...candidate,
      sources: Object.freeze(candidate.sources.map((source) => Object.freeze({ ...source }))),
    })
  )
);

/**
 * Returns ranked discovery candidate suppliers up to the requested limit.
 */
function getDiscoverySuppliers({ limit = 5 } = {}) {
  return discoveryCandidates.slice(0, limit);
}

module.exports = Object.freeze({
  discoveryCandidates,
  getDiscoverySuppliers,
});
