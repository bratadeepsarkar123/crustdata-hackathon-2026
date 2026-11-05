'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { parseRequest } = require('./request-reader.cjs');
const { sampleRequests } = require('../../samples/requests.cjs');

test('parses all simulated request fixtures to the exact shared shape', () => {
  for (const sample of sampleRequests) {
    assert.equal(sample.label, 'SIMULATED');
    assert.deepEqual(parseRequest(sample.text), sample.request);
  }
});

test('leaves ambiguous amounts, currencies, and regions unresolved', () => {
  const cases = [
    {
      text: 'Need 500 sensors, budget between USD 10 and 20.',
      field: 'budget',
    },
    {
      text: 'Need 500 sensors; budget USD 100 per item.',
      field: 'budget',
    },
    {
      text: 'Need 2 sensors for Pune. Budget USD 500 to 1000.',
      field: 'budget',
    },
    {
      text: 'Need 2 sensors for Pune. Budget around USD 500.',
      field: 'budget',
    },
    {
      text: 'Need 2 sensors for Pune. Budget \u20ac100; quote in USD.',
      field: 'budget',
      alsoMissing: 'currency',
    },
    {
      text: 'Need 2 sensors for Pune. Budget is $500.',
      field: 'budget',
      alsoMissing: 'currency',
    },
    {
      text: 'Need 2 sensors delivered to Bengaluru or Pune within 14 days.',
      field: 'region',
    },
    {
      text: 'Need 2 sensors delivered to Bengaluru, Pune within 14 days.',
      field: 'region',
    },
  ];

  for (const { text, field, alsoMissing } of cases) {
    const request = parseRequest(text);
    assert.equal(request[field], null, `${field} should be unresolved for: ${text}`);
    assert.ok(request.missing_fields.includes(field));
    if (alsoMissing) {
      assert.equal(request[alsoMissing], null, `${alsoMissing} should be unresolved for: ${text}`);
      assert.ok(request.missing_fields.includes(alsoMissing));
    }
  }
});

test('leaves ranged quantities and deadlines unresolved', () => {
  const quantityRanges = [
    'Need 500 or 600 sensors for Kanpur. Budget USD 25000; delivery within 14 days.',
    'Need 500 to 600 sensors for Kanpur. Budget USD 25000; delivery within 14 days.',
  ];
  for (const text of quantityRanges) {
    const request = parseRequest(text);
    assert.equal(request.item, null);
    assert.equal(request.quantity, null);
    assert.ok(request.missing_fields.includes('item'));
    assert.ok(request.missing_fields.includes('quantity'));
  }

  const deadlineAlternatives = [
    'Need 500 sensors for Kanpur. Budget USD 25000; within 2 weeks or 3 weeks.',
    'Need 500 sensors for Kanpur. Budget USD 25000; within 2 weeks or 3.',
  ];
  for (const text of deadlineAlternatives) {
    const request = parseRequest(text);
    assert.equal(request.deadline_days, null);
    assert.ok(request.missing_fields.includes('deadline_days'));
  }
});
