'use strict';

// Policy check: total within budget and lead time within the delivery deadline.
// Returns the same shape as the fixture policy_decision (label, approved, display_label, reason).
function checkPolicy({ request, quote }) {
  const reasons = [];
  const missing = Array.isArray(request.missing_fields) ? request.missing_fields : [];
  if (missing.length > 0 || !Number.isFinite(request.quantity)) {
    reasons.push(`the request is incomplete (missing: ${missing.join(', ') || 'quantity'})`);
    return Object.freeze({
      label: 'SIMULATED',
      approved: false,
      display_label: quote.display_label,
      reason: `SIMULATED policy check: rejected because ${reasons.join(' and ')}.`,
    });
  }
  const total = quote.unit_price * request.quantity;
  if (quote.lead_time_days > request.deadline_days) {
    reasons.push(`lead time ${quote.lead_time_days} days is over the ${request.deadline_days}-day deadline`);
  }
  if (total > request.budget) {
    reasons.push(`total ${total} is over the budget of ${request.budget}`);
  }
  const approved = reasons.length === 0;
  return Object.freeze({
    label: 'SIMULATED',
    approved,
    display_label: quote.display_label,
    reason: approved
      ? 'SIMULATED policy check: total is within budget and lead time is within the deadline.'
      : `SIMULATED policy check: rejected because ${reasons.join(' and ')}.`,
  });
}

/**
 * Task 3: Evaluate quote with granular status: approve, hold, or reject.
 * Includes explicit rule that flags "MOQ not verified" as a hold.
 */
function evaluatePolicyDecision({ request, quote, supplier, options = {} }) {
  // Check for hold conditions (e.g. MOQ not verified)
  const isMoqUnverified =
    options.moq_verified === false ||
    options.moq_status === 'UNVERIFIED' ||
    Boolean(quote && quote.moq_verified === false) ||
    Boolean(supplier && supplier.product_line_status === 'HUMAN_OR_SIMULATED');

  if (isMoqUnverified) {
    return Object.freeze({
      label: 'SIMULATED',
      status: 'HOLD',
      approved: false,
      display_label: quote.display_label,
      reason: 'HOLD: MOQ not verified',
    });
  }

  // Check standard policy rules (budget, deadline, missing fields)
  const baseDecision = checkPolicy({ request, quote });
  if (!baseDecision.approved) {
    return Object.freeze({
      label: 'SIMULATED',
      status: 'REJECT',
      approved: false,
      display_label: quote.display_label,
      reason: baseDecision.reason,
    });
  }

  return Object.freeze({
    label: 'SIMULATED',
    status: 'APPROVE',
    approved: true,
    display_label: quote.display_label,
    reason: 'APPROVE: total is within budget and lead time is within deadline.',
  });
}

/**
 * Compare all candidate quotes against request policy.
 * Compliant quotes are ranked. Non-compliant quotes (over budget, lead time exceeded, etc.)
 * are routed directly to the exceptions queue with the detailed failure reason.
 */
function evaluateQuotesPolicy({ request, quotes }) {
  if (!Array.isArray(quotes)) {
    throw new TypeError('quotes must be an array');
  }

  const approvedCandidates = [];
  const exceptionsQueue = [];

  for (const quote of quotes) {
    const decision = checkPolicy({ request, quote });
    if (decision.approved) {
      approvedCandidates.push({
        display_label: quote.display_label,
        quote,
        decision,
        total: quote.unit_price * request.quantity,
        label: 'SIMULATED',
      });
    } else {
      exceptionsQueue.push({
        display_label: quote.display_label,
        quote,
        reason: decision.reason,
        label: 'SIMULATED',
      });
    }
  }

  // Rank approved by total cost ascending, then lead time ascending
  approvedCandidates.sort((a, b) => {
    if (a.total !== b.total) return a.total - b.total;
    return a.quote.lead_time_days - b.quote.lead_time_days;
  });

  return Object.freeze({
    label: 'SIMULATED',
    approved_candidates: Object.freeze(approvedCandidates),
    exceptions_queue: Object.freeze(exceptionsQueue),
    best_candidate: approvedCandidates.length > 0 ? approvedCandidates[0] : null,
  });
}

module.exports = {
  checkPolicy,
  evaluatePolicyDecision,
  evaluateQuotesPolicy,
};
