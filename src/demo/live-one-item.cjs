'use strict';
// One-item LIVE demo. Calls the Crustdata company search API with the owner's own key.
// Node 18+ (global fetch). No dependencies.
//
// Usage (PowerShell, in the repo folder):
//   $env:CRUSTDATA_API_KEY = "<your key>"
//   node src/demo/live-one-item.cjs --query "sintered neodymium magnet manufacturer" --limit 5
//
// Display (owner decision, 2026-11-06): each supplier shows the company name, website and the
// full self-reported description exactly as the live response returned it. Nothing is filtered.
// Terms for showing company names are not confirmed. Check the Crustdata data-export terms before publishing.

const ENDPOINT = 'https://api.crustdata.com/company/search';
const API_VERSION = '2025-11-01';
const DEFAULT_QUERY = 'sintered neodymium magnet manufacturer';
const DEFAULT_LIMIT = 5;
const MAX_LIMIT = 10;
const LIVE_SOURCE = '[LIVE Crustdata POST /company/search; self-reported]';
const MAX_DESCRIPTION_CHARS = 200;

// Phrases that would break the display rule. A description containing any of these is withheld.
// Covers names of places (words such as city, province, country), founding years and phrases like
// "since 1995" or "20 years", size words (employees, staff, workers, capacity, tons) and links.
const WITHHOLD_PATTERN = /headquarter|head office|located|based in|\bcity\b|province|\bstate\b|\bcountry\b|\bregion\b|employee|staff|headcount|workers|founded|establish|\bsince\b|\byears?\b|\b(19|20)\d{2}\b|\bcapacity\b|\btons?\b|\bhttps?:|www\.|\.com\b|\.in\b|@/i;

function parseArgs(argv) {
  const out = { query: DEFAULT_QUERY, limit: DEFAULT_LIMIT, help: false };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--help' || a === '-h') out.help = true;
    else if (a === '--query') out.query = String(argv[++i] || '').trim();
    else if (a === '--limit') out.limit = Number(argv[++i]);
    else throw new Error(`Unknown option: ${a}`);
  }
  if (!out.query) throw new Error('--query must not be empty');
  if (!Number.isInteger(out.limit) || out.limit < 1 || out.limit > MAX_LIMIT) {
    throw new Error(`--limit must be a whole number from 1 to ${MAX_LIMIT}`);
  }
  return out;
}

function buildRequest({ query, limit, apiKey }) {
  return {
    url: ENDPOINT,
    init: {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'x-api-version': API_VERSION,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        search: { query, mode: 'hybrid' },
        limit,
        fields: ['basic_info'],
      }),
    },
  };
}

// Self-reference ("we", "our", "the company") is dropped too, since it points at the company.
const SELF_REFERENCE_PATTERN = /\b(we|our|us|the company|this company)\b/i;

// Keeps only the sentences that carry no name, place, year, size word, link or self-reference.
// Returns a display-safe string, or null when there is no description at all.
// If no sentence survives, the whole description is withheld.
function safeDescription(company) {
  const bi = company && typeof company.basic_info === 'object' && company.basic_info ? company.basic_info : company || {};
  const raw = typeof bi.description === 'string' ? bi.description.trim() : '';
  if (!raw) return null;
  const name = typeof bi.name === 'string' ? bi.name.trim().toLowerCase() : '';
  const sentences = raw.split(/(?<=[.!?。])\s+/).map((s) => s.trim()).filter(Boolean);
  const kept = sentences.filter((s) => {
    if (WITHHOLD_PATTERN.test(s) || SELF_REFERENCE_PATTERN.test(s)) return false;
    if (name.length > 2 && s.toLowerCase().includes(name)) return false;
    return true;
  });
  if (kept.length === 0) return 'description withheld (no sentence free of name, location, size or link)';
  const text = kept.join(' ');
  return text.length > MAX_DESCRIPTION_CHARS ? `${text.slice(0, MAX_DESCRIPTION_CHARS)}...` : text;
}

function render(json, { query }) {
  const companies = Array.isArray(json && json.companies) ? json.companies
    : Array.isArray(json && json.results) ? json.results
    : [];
  const lines = [];
  lines.push('ONE-ITEM SOURCING DEMO (LIVE)');
  lines.push(`Search: ${query}`);
  lines.push('');
  if (companies.length === 0) {
    lines.push('No companies returned for this search. Try a different --query.');
    return { text: lines.join('\n'), count: 0 };
  }
  lines.push('Shortlist:');
  companies.forEach((c, i) => {
    const bi = c && typeof c.basic_info === 'object' && c.basic_info ? c.basic_info : {};
    const name = typeof bi.name === 'string' && bi.name.trim() ? bi.name.trim() : 'name not returned';
    const domain = typeof bi.primary_domain === 'string' && bi.primary_domain.trim() ? bi.primary_domain.trim() : 'website not returned';
    const desc = typeof bi.description === 'string' && bi.description.trim() ? bi.description.trim() : 'no self-reported description returned';
    lines.push(`  Supplier ${i + 1}: ${name}`);
    lines.push(`    Website: ${domain}`);
    lines.push(`    Description: ${desc}`);
    lines.push(`    cited: basic_info.name, basic_info.primary_domain, basic_info.description ${LIVE_SOURCE}`);
  });
  lines.push('');
  lines.push('Still not verified: minimum order size, sole-source status, thin 3 mm capability.');
  lines.push('LIVE - descriptions are self-reported by each company. No company contacted, no email sent.');
  return { text: lines.join('\n'), count: companies.length };
}

const USAGE = [
  'Live one-item sourcing search (Crustdata).',
  '',
  'Set your key first in this terminal (PowerShell):',
  '  $env:CRUSTDATA_API_KEY = "<your key>"',
  '',
  'Then run:',
  '  node src/demo/live-one-item.cjs --query "sintered neodymium magnet manufacturer" --limit 5',
].join('\n');

async function run({ argv = [], env = process.env, fetchImpl = globalThis.fetch, stdout = console.log, stderr = console.error } = {}) {
  let opts;
  try {
    opts = parseArgs(argv);
  } catch (err) {
    stderr(`ERROR: ${err.message}`);
    stderr(USAGE);
    return 2;
  }
  if (opts.help) {
    stdout(USAGE);
    return 0;
  }
  const apiKey = (env.CRUSTDATA_API_KEY || '').trim();
  if (!apiKey) {
    stderr('ERROR: CRUSTDATA_API_KEY is not set in this terminal.');
    stderr('Set it with:  $env:CRUSTDATA_API_KEY = "<your key>"  and run the command again.');
    return 2;
  }
  if (typeof fetchImpl !== 'function') {
    stderr('ERROR: this Node version has no fetch. Use Node 18 or newer.');
    return 2;
  }

  const { url, init } = buildRequest({ query: opts.query, limit: opts.limit, apiKey });
  let res;
  try {
    res = await fetchImpl(url, init);
  } catch (err) {
    stderr(`ERROR: could not reach Crustdata (${err.message}). Check the internet connection and try again.`);
    return 1;
  }
  if (!res.ok) {
    // Print status only. Never print headers or the key.
    let detail = '';
    try {
      const body = await res.json();
      detail = body && (body.message || body.error) ? String(body.message || body.error) : '';
    } catch (_) { /* body is not JSON */ }
    stderr(`ERROR: Crustdata returned HTTP ${res.status}${detail ? `: ${detail}` : ''}.`);
    if (res.status === 401 || res.status === 403) stderr('Check that CRUSTDATA_API_KEY is the right key and that the plan allows search.');
    if (res.status === 402) stderr('The account is out of credits. Top up before the demo.');
    if (res.status === 429) stderr('Rate limit reached. Wait a minute and try again.');
    return 1;
  }

  let json;
  try {
    json = await res.json();
  } catch (_) {
    stderr('ERROR: Crustdata returned a response that is not JSON.');
    return 1;
  }
  const { text } = render(json, { query: opts.query });
  stdout(text);
  return 0;
}

module.exports = { parseArgs, buildRequest, safeDescription, render, run, ENDPOINT, API_VERSION, LIVE_SOURCE };

if (require.main === module) {
  run({ argv: process.argv.slice(2) }).then((code) => { process.exitCode = code; });
}
