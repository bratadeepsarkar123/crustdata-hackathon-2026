'use strict';

const sampleRequests = Object.freeze([
  Object.freeze({
    label: 'SIMULATED',
    text: 'Need 500 industrial temperature sensors delivered to Bengaluru within 14 days. Budget is $25,000 total; quote in USD.',
    request: Object.freeze({
      item: 'industrial temperature sensors',
      quantity: 500,
      budget: 25000,
      currency: 'USD',
      deadline_days: 14,
      region: 'Bengaluru',
      missing_fields: Object.freeze([]),
    }),
  }),
  Object.freeze({
    label: 'SIMULATED',
    text: 'We need 120 pressure transmitters for our Pune plant; keep total spend below ₹18 lakh and deliver inside 30 days.',
    request: Object.freeze({
      item: 'pressure transmitters',
      quantity: 120,
      budget: 1800000,
      currency: 'INR',
      deadline_days: 30,
      region: 'Pune',
      missing_fields: Object.freeze([]),
    }),
  }),
  Object.freeze({
    label: 'SIMULATED',
    text: 'Please source 250 PT100 RTD probes for Kanpur. Maximum ₹7.5 lakh all-in.',
    request: Object.freeze({
      item: 'PT100 RTD probes',
      quantity: 250,
      budget: 750000,
      currency: 'INR',
      deadline_days: null,
      region: 'Kanpur',
      missing_fields: Object.freeze(['deadline_days']),
    }),
  }),
]);

module.exports = Object.freeze({
  label: 'SIMULATED',
  sampleRequests,
});
