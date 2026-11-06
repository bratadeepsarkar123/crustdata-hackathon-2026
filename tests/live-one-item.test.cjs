'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { run, buildRequest, safeDescription, render, parseArgs, ENDPOINT, API_VERSION, LIVE_SOURCE } = require('../src/demo/live-one-item.cjs');

const KEY = 'test-key-do-not-print-123';

function mockFetch(status, body) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url, init });
    return {
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
    };
  };
  fn.calls = calls;
  return fn;
}

function captured() {
  const out = [];
  const err = [];
  return { out, err, stdout: (m) => out.push(String(m)), stderr: (m) => err.push(String(m)) };
}

const SAMPLE = {
  companies: [
    {
      basic_info: {
        name: 'Acme Magnetics Pvt Ltd',
        primary_domain: 'acmemagnetics.com',
        description: 'Sintered NdFeB magnet maker offering custom shapes, fast turnaround and ISO 9001 quality system.',
      },
    },
    {
      basic_info: {
        name: 'Beta Rare Earth Co',
        primary_domain: 'betarare.in',
        description: 'Beta Rare Earth is headquartered in Shandong and has 500 employees making permanent magnets.',
      },
    },
    {
      basic_info: { name: 'Gamma Works', primary_domain: 'gammaworks.in' },
    },
  ],
};

test('request uses the company search endpoint with the two required headers and ranked hybrid search', () => {
  const req = buildRequest({ query: 'magnet maker', limit: 5, apiKey: KEY });
  assert.strictEqual(req.url, 'https://api.crustdata.com/company/search');
  assert.strictEqual(ENDPOINT, req.url);
  assert.strictEqual(req.init.method, 'POST');
  assert.strictEqual(req.init.headers.Authorization, `Bearer ${KEY}`);
  assert.strictEqual(req.init.headers['x-api-version'], API_VERSION);
  assert.strictEqual(API_VERSION, '2025-11-01');
  const body = JSON.parse(req.init.body);
  assert.deepStrictEqual(body.search, { query: 'magnet maker', mode: 'hybrid' });
  assert.strictEqual(body.limit, 5);
  assert.deepStrictEqual(body.fields, ['basic_info']);
});

test('display never shows company names, domains, locations, headcount or founding details', () => {
  const { text } = render(SAMPLE, { query: 'magnet maker' });
  for (const s of ['Acme Magnetics', 'Beta Rare Earth Co', 'Gamma Works', 'acmemagnetics', 'betarare', 'gammaworks',
    'http', 'www.', '.com', '.in', 'Shandong', 'headquartered', 'employees', '500', 'founded']) {
    assert.ok(!text.includes(s), `leaked: ${s}`);
  }
});

test('safe description is shown, unsafe ones are withheld, missing ones are reported', () => {
  const { text, count } = render(SAMPLE, { query: 'magnet maker' });
  assert.strictEqual(count, 3);
  assert.ok(text.includes('Supplier 1: Sintered NdFeB magnet maker offering custom shapes'));
  assert.ok(text.includes('Supplier 2: description withheld (contains a name, link, location or size detail)'));
  assert.ok(text.includes('Supplier 3: no self-reported description returned'));
});

test('every citation line carries the LIVE self-reported label, and no simulated label is used', () => {
  const { text } = render(SAMPLE, { query: 'magnet maker' });
  const cited = text.split('\n').filter((l) => l.includes('cited:'));
  assert.strictEqual(cited.length, 3);
  for (const l of cited) assert.ok(l.includes(LIVE_SOURCE), l);
  assert.ok(!text.includes('SIMULATED'));
});

test('description that repeats the company name is withheld even without other patterns', () => {
  const s = safeDescription({ basic_info: { name: 'Delta Magnets', description: 'Delta Magnets makes sintered magnets.' } });
  assert.strictEqual(s, 'description withheld (contains the company name)');
});

test('long descriptions are truncated', () => {
  const long = 'a'.repeat(400);
  const s = safeDescription({ basic_info: { description: long } });
  assert.ok(s.endsWith('...'));
  assert.ok(s.length <= 204);
});

test('zero results print a clear message and no supplier lines', () => {
  const { text, count } = render({ companies: [] }, { query: 'nothing' });
  assert.strictEqual(count, 0);
  assert.ok(text.includes('No companies returned'));
  assert.ok(!text.includes('Supplier 1'));
});

test('missing key exits 2 with a clear message and never calls the network', async () => {
  const io = captured();
  const f = mockFetch(200, SAMPLE);
  const code = await run({ argv: [], env: {}, fetchImpl: f, stdout: io.stdout, stderr: io.stderr });
  assert.strictEqual(code, 2);
  assert.strictEqual(f.calls.length, 0);
  assert.ok(io.err.join('\n').includes('CRUSTDATA_API_KEY is not set'));
  assert.ok(io.err.join('\n').includes('$env:CRUSTDATA_API_KEY'));
});

test('successful run prints the shortlist, exits 0, and never prints the key', async () => {
  const io = captured();
  const f = mockFetch(200, SAMPLE);
  const code = await run({ argv: ['--query', 'magnet maker', '--limit', '3'], env: { CRUSTDATA_API_KEY: KEY }, fetchImpl: f, stdout: io.stdout, stderr: io.stderr });
  assert.strictEqual(code, 0);
  assert.strictEqual(f.calls.length, 1);
  const all = io.out.join('\n') + io.err.join('\n');
  assert.ok(all.includes('Supplier 1'));
  assert.ok(!all.includes(KEY), 'key must never be printed');
});

test('HTTP 401 exits 1 with the status and no key in the output', async () => {
  const io = captured();
  const f = mockFetch(401, { message: 'invalid key' });
  const code = await run({ argv: [], env: { CRUSTDATA_API_KEY: KEY }, fetchImpl: f, stdout: io.stdout, stderr: io.stderr });
  assert.strictEqual(code, 1);
  const all = io.err.join('\n');
  assert.ok(all.includes('HTTP 401'));
  assert.ok(all.includes('invalid key'));
  assert.ok(!all.includes(KEY));
});

test('network failure exits 1 with a clear message', async () => {
  const io = captured();
  const f = async () => { throw new Error('getaddrinfo ENOTFOUND'); };
  const code = await run({ argv: [], env: { CRUSTDATA_API_KEY: KEY }, fetchImpl: f, stdout: io.stdout, stderr: io.stderr });
  assert.strictEqual(code, 1);
  assert.ok(io.err.join('\n').includes('could not reach Crustdata'));
});

test('bad arguments exit 2', async () => {
  const io = captured();
  const code = await run({ argv: ['--limit', '50'], env: { CRUSTDATA_API_KEY: KEY }, fetchImpl: mockFetch(200, SAMPLE), stdout: io.stdout, stderr: io.stderr });
  assert.strictEqual(code, 2);
  assert.ok(io.err.join('\n').includes('--limit must be'));
  assert.throws(() => parseArgs(['--bogus']), /Unknown option/);
});
