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

module.exports = { checkPolicy };
