'use strict';
// One-item demo screen. Offline, no dependencies. SIMULATED.
const fs = require('node:fs');
const path = require('node:path');

// Every citation shown on screen carries this label (README: "marked as a simulated fixture source").
const SIMULATED_SOURCE = '[SIMULATED fixture; no live Crustdata call]';

function render(data) {
  const { item, constraints: c } = data;
  const out = [];
  out.push('ONE-ITEM SOURCING DEMO');
  out.push(`Item: ${item.name}, ${item.thickness_mm} mm thick, ${item.quantity_pcs} pcs, buyer in ${item.buyer_location}`);
  out.push(`Constraints: supplier in ${c.supplier_country}, sole source: ${c.sole_source ? 'yes' : 'no'}, MOQ: ${c.moq}`);
  out.push('');
  out.push('Shortlist:');
  for (const s of data.suppliers) {
    for (const cl of s.claims) {
      out.push(`  ${s.label}: ${cl.text}`);
      out.push(`    cited: ${cl.citation} ${SIMULATED_SOURCE}`);
    }
  }
  out.push('');
  out.push(`Recommended: ${data.recommended_label}`);
  out.push(`  Reason: ${data.reason} ${SIMULATED_SOURCE}`);
  out.push(`  Top risk: ${data.top_risk} ${SIMULATED_SOURCE}`);
  out.push('');
  out.push('Still not verified:');
  for (const u of data.unverified) out.push(`  - ${u}`);
  out.push('');
  out.push('SIMULATED - no company contacted, no email sent');
  return out.join('\n');
}

function load(file) {
  const p = file || path.join(__dirname, '..', '..', 'samples', 'one-item', 'supplier-shortlist.json');
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

module.exports = { render, load };
if (require.main === module) console.log(render(load()));
