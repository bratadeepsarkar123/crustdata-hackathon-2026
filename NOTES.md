# Issue #6 — acceptance checks and verification plan

Status: **DONE** for the offline steps 1–7 harness and IP0 contracts/fixtures. Acceptance plan was recorded before implementation. Source of truth: `docs/handoffs/MASTER-HANDOFF-supplier.md`, sections 4–6, and the assigned issue #6 task brief. The integrator confirmed issue #6 and related issue bodies using the signed-in owner account with process-scoped authentication; no account switch was made.

## Acceptance checks

1. **Request parsing and contract** — intake parses all three realistic sample request texts into the exact section 6 fields: `item`, `quantity`, `budget`, `currency`, `deadline_days`, `region`, and `missing_fields` (array). Missing values remain `null` and their field names appear in `missing_fields`; no value is guessed. Each fixture is labelled `SIMULATED` outside the request object so its normalized shape stays exact.
2. **Candidate and verified supplier contract** — records carry exactly the shared fields: `display_label`, `name_internal`, `primary_domain`, `year_founded`, `headquarters_internal`, `headcount_total_internal`, `industry`, `product_line_status` (`CONFIRMED` or `HUMAN_OR_SIMULATED`), `sources` (`field`, `endpoint` pairs), and `confidence`. `name_internal` and `confidence` may be `null` when explicitly unknown. `display_label` is the sole supplier identifier permitted on screen; `_internal` fields are internal-only.
3. **WhatsApp message contract** — records match the shared shape: `display_label`, `direction` (`outbound` or `inbound`), `text`, `idempotency_key`, `mode` (`TEAM_PHONE` or `SIMULATED`), and `label`. Simulated messages carry the literal `SIMULATED` label.
4. **Quote contract** — records match `display_label`, `unit_price`, `lead_time_days`, and `label: "SIMULATED"`.
5. **Vendor record / PO contract** — records match `idempotency_key`, `display_label`, `po_number`, `total`, `status`, and `label: "SIMULATED"`.
6. **Display projection** — screen-facing supplier facts contain only the neutral `display_label` and citations (`field`, `endpoint`); no company values, real/internal names, `_internal` fields, raw records, or other identifiers. Citation field names and endpoint paths are allowlisted and canonicalized. Feed the projection a supplier with distinct sentinel values for every private field and assert none of the sentinels or private keys appear in serialized screen output; reject an injected internal name or a citation endpoint containing a URL/query.
7. **Offline end-to-end fixture** — run a sample request through steps 1–7 without network calls, using the labelled fixture with fictional suppliers, citations, simulated quotes, and a predetermined chosen supplier. Verify on-screen output contains only supplier labels and field/endpoint citations, and every simulated output is marked `SIMULATED`. Keep real/internal names only in the internal log.
8. **Write idempotency** — vendor and PO writes use separate unique idempotency keys. For each write, persist/check its key before performing the write. Verify a retry after success, a simulated crash after key persistence, and concurrent attempts create at most one vendor record and at most one PO. A missing-required-field or policy-exception path creates no PO.
9. **Runtime validation** — plain modern Node.js CommonJS, no dependencies. Validators accept valid shared shapes and reject missing required fields, invalid enums, malformed `missing_fields`/`sources`, and simulated records without their required `SIMULATED` label.

## Exact verification plan

- Run CommonJS `node -e` assertions for valid request, supplier, WhatsApp, quote, vendor-record and PO-compatible shapes. For each enum-bearing shape, assert invalid enum values fail; assert missing required keys and invalid nullable/missing-field combinations fail.
- Require all three sample request fixtures and the full-flow fixture. Assert every wrapper is `SIMULATED`, each normalized request has exactly the section 6 keys, expected outputs match the intake parser, and unresolved fields remain null and are named in `missing_fields`. Region values preserve only the explicit city named by the request; no country is inferred.
- Project supplier records containing unique sentinels in all company/internal fields. Serialize the result and assert only `display_label` and canonical citations (`field`, `endpoint`) remain; assert no sentinel values, internal keys, raw identifiers, or company-value properties appear. Assert citations containing an injected internal name, arbitrary field, full URL, or URL query are rejected before projection.
- Run the full-flow fixture offline and assert steps 1–7 complete, no network call is made, selected supplier matches the predetermined neutral label, and all output screens contain labels/citations only with simulated items labelled `SIMULATED`.
- Exercise vendor and PO writes independently with deterministic keys: normal repeat, crash after key persistence, and concurrent same-key attempts each leave a single record. Exercise missing/exception handling and assert zero POs are written.
- Run Node.js directly with no package installation. Confirm sample/contract imports do not import or invoke networking code.

## Proposed shared exports (for teammate coordination)

- `src/contracts/index.cjs`: `validateRequest`, `validateSupplier`, `validateWhatsAppMessage`, `validateQuote`, `validateVendorRecord`, and `toSupplierDisplay`. Validators return `{ valid, errors }`; allowed shared-shape keys and citation pairs are strict. The projection canonicalizes citations from the allowlist and returns only `{ display_label, sources: [{ field, endpoint }] }`.
- `samples/requests.cjs`: three `SIMULATED` request-text fixtures with expected normalized Request shapes and explicit city-only regions.
- `samples/full-flow.cjs`: one `SIMULATED` offline fixture referencing the first exact `sampleRequests` request text and expected normalized Request; includes fictional exact-shape supplier records, a separate simulated `quotes` array, a clearly simulated stub policy decision with predetermined chosen supplier, and no pre-generated vendor/PO records (the writer owns those writes).

The JSON fields and enums above are frozen to section 6; export names/wrapper layout are implementation details coordinated with the integrator and intake owner.

## Implemented result and final checks

- `src/contracts/index.cjs` provides strict CommonJS runtime validators and a supplier display projection limited to neutral labels and allowlisted canonical citations.
- `samples/requests.cjs` has three fabricated `SIMULATED` request texts and exact expected normalized requests. All three parse without guessing; the Kanpur sample retains a null deadline and lists it in `missing_fields`.
- `samples/full-flow.cjs` provides one fabricated complete flow. `quote_currency_by_label` supplies explicit currency metadata outside the frozen quote records. The first request is the only sample that has the complete steps 1–7 fixture; the other two parse but cannot produce a PO in this harness.
- `src/orchestrator.cjs` runs stage 1 with the local parser; stages 2–6 consume only prerecorded `SIMULATED` fixture data; stage 7 calls the idempotent local writer. It verifies exact sample text and expected parser output, requires an exact quote-currency map, stops before writing on missing/mismatched data or an unapproved decision, displays only labels/citations for suppliers, and never prints arbitrary policy reasons or supplier values. Quote and vendor/PO display wrappers show currency and a simulated source without changing section-6 record shapes.
- `tests/e2e.cjs` covers the three samples, offline stage 1–7 run, no-network guard, idempotent repeat, invalid inputs and fixtures, policy/quote/currency failures, safe state paths, and supplier-value/citation privacy.
- Run the complete suite from a checkout outside the OS temporary directory; test 10 checks a checkout-derived path outside temp and is skipped when the checkout is within temp.
- `README.md` explains the service hypothesis, current scope and limits, commands, source handling, approaches, next integration work, and owner commit/push rule. `samples/sample-run.json` is sanitized first-run CLI evidence.

Final verification: `node --test tests/e2e.cjs src/po/writer.test.cjs src/state/idempotency.test.cjs` passed **22/22**. The final combined command, including intake component tests, also passed **25/25**: `node --test tests/e2e.cjs src/intake/request-reader.test.cjs src/po/writer.test.cjs src/state/idempotency.test.cjs`. `node --check src/orchestrator.cjs` and `node --check tests/e2e.cjs` passed. The CLI succeeded with both a fresh default temporary state directory and an explicit temporary state directory; both returned separate vendor/PO records with `CREATED` status on first run. The sample evidence was parsed and checked for internal names, domains, headquarters, and `name_internal` leakage. No network call, commit, or push was made.

Known limitation: this is fixture-only. Discovery, verification, real dedupe, WhatsApp, policy logic, and human exception routing are not integrated here. No real supplier contact or Crustdata request occurs.
# Engineering Notes - Person 2 (Discovery & Crustdata)
**Owner:** Aditya Chittora (`AdityaChittora`)  
**Issue:** #7 | **Branch:** `feat/issue-7-discovery` | **PR:** #9  
**Source of Truth:** `docs/handoffs/MASTER-HANDOFF-supplier.md` & `src/contracts/index.cjs` (PR #10)

---

## 1. What Works
- **Crustdata API Client (`src/crustdata/client.py`)**:
  - Headers: `Authorization: Bearer <KEY>`, `x-api-version: 2025-11-01`.
  - HTTP 429 backoff: respects `Retry-After` header and backs off exponentially.
  - HTTP 402/403 immediate stopping: raises `CrustdataCreditsExhaustedError` and `CrustdataPlanGatedError` without retrying.
  - Secrets safety: reads only from `CRUSTDATA_API_KEY` with git-ignore check; keys are masked in logs/repr.
- **Credit Safety & In-Run Budget Guard (`src/crustdata/credits.py`)**:
  - Pre-flight balance check: calls `check_account_credits` and fails closed if credits are below budget.
  - In-run usage tracking: records credit cost after each search, identify, and enrich call.
  - Hard budget ceiling: stops immediately if the budget is reached (verified with 100-candidate test).
- **Candidate Discovery - Step 2 (`src/discovery/candidate_search.py`)**:
  - Ranked search (`search.query`) first, location filters as hard limits, `company_autocomplete` before industry filtering.
  - Single 100-result window with filters-only fallback.
- **Supplier Verification - Step 3 (`src/discovery/verify.py`)**:
  - Free `POST /company/identify` first (hard guard forbids requesting headcount/locations on identify).
  - `POST /company/enrich` (2 credits) for `headcount.total`, `locations.headquarters`, and `basic_info.description`.
  - Product-line status: marks `CONFIRMED` when description is populated, `HUMAN_OR_SIMULATED` when empty.
  - 402/403/429 errors re-raise immediately, terminating the loop after 1 attempt.
- **Deduplication - Step 4 (`src/discovery/dedupe.py`)**:
  - Domain and company name normalization, token & sequence similarity matching, and entity merging with confidence score.
- **Contract Compatibility (`src/contracts/index.cjs` on `feat/issue-6-integrator` / PR #10)**:
  - Outputs exact 10 keys: `display_label`, `name_internal`, `primary_domain`, `year_founded`, `headquarters_internal`, `headcount_total_internal`, `industry`, `product_line_status`, `sources`, `confidence`.
  - Sources use exact allowlisted fields (`primary_domain`, `year_founded`, `headcount.total`, `locations.headquarters`, `basic_info.description`) and endpoints.
  - Validated 100% against Person 1's `validateSupplier` and `toSupplierDisplay` in Node.js.
- **Option C Screen Display (`src/discovery/service.py`, `demo_citations.py`)**:
  - Screens and stdout show display labels (`Supplier 1`, ...) and citations only.
  - Real company names, domains, HQ and headcount are strictly kept in `discovery_internal_audit.log` (git-ignored) and never printed to stdout or stderr.
  - Run command: plain `python demo_citations.py`.

---

## 2. What Is Fixture-Only
- All default tests and demo runs operate offline using realistic fixtures in `src/discovery/fixtures.py` (5 industrial temperature sensor manufacturers: Tempsens, Radix, Baumer, Pyrosales, Sensorcon).
- The demo runs on fixtures only. Do not start live calls. Wait for the owner's go before anything live.
- No API keys or network connection required to run tests or the demo script.

---

## 3. What Needs the Owner's Go for Live Calls
- Setting `CRUSTDATA_API_KEY` in local environment.
- Owner approval for the single live Crustdata run (IP3).
- Verification with `GET /account/credits` before triggering live calls (run budget is ~10.60 credits, well under the 200 limit).

---

## 4. Test Suite (33 Tests Passing)
Run all Person 2 tests:
```powershell
python -m unittest discover -s tests -p "crustdata*.py"
```
Execute demo citation script:
```powershell
python demo_citations.py
```
