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
