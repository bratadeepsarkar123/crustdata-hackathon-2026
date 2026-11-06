'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { render, load } = require('../src/demo/one-item.cjs');

const data = load();
const text = render(data);

test('output has required sections', () => {
  for (const s of ['Supplier 1', 'Recommended', 'SIMULATED']) assert.ok(text.includes(s), s);
  assert.ok(text.toLowerCase().includes('not verified'));
});

test('output has no links or domains', () => {
  for (const s of ['http', 'www.', '.com']) assert.ok(!text.includes(s), s);
});

test('sample JSON has five suppliers and Supplier 1 recommended', () => {
  assert.strictEqual(data.suppliers.length, 5);
  assert.strictEqual(data.recommended_label, 'Supplier 1');
});

test('no company location, headcount or founding-year values on screen (README rule)', () => {
  for (const s of ['founded', 'staff', 'headquarters', 'HQ', 'Shandong', 'employee', 'employee_count', '201-500', '5001', 'year_founded', 'locations.', 'Small', 'Large', 'very large']) {
    assert.ok(!text.includes(s), s);
  }
});

test('every cited line carries the simulated-fixture label', () => {
  const cited = text.split('\n').filter((l) => l.includes('cited:') || l.includes('Reason:') || l.includes('Top risk:'));
  assert.ok(cited.length > 0);
  for (const l of cited) assert.ok(l.includes('[SIMULATED fixture; no live Crustdata call]'), l);
});
