# Engineering Notes - Person 2 (Discovery & Crustdata)
**Owner:** Aditya Chittora (`AdityaChittora`)
**Issue:** #7: Person 2: discovery and Crustdata (steps 2 to 4)
**Branch:** `feat/issue-7-discovery`
**Source of Truth:** `docs/handoffs/MASTER-HANDOFF-supplier.md` on branch `docs/corrected-crustdata-handoff` (sections 4, 5, 6, 7, 12).

---

## 1. Acceptance Checks & Verification Plan

| # | Acceptance Check (Issue #7 & Section 4/5/7/8) | Verification Method | Associated Test / Script |
|---|---|---|---|
| 1 | **Client Headers & Base URL:** Base `https://api.crustdata.com`, `Authorization: Bearer <KEY>`, `x-api-version: 2025-11-01`. | Unit test verifying header composition and URL construction without leaking keys. | `tests/test_crustdata_client.py::test_client_headers` |
| 2 | **429 Backoff:** On HTTP 429, back off and retry respecting retry-after headers or exponential backoff up to max attempts. | Mock 429 then 200, verifying sleep intervals and eventual success. | `tests/test_crustdata_client.py::test_client_429_backoff` |
| 3 | **402 & 403 Stop Immediately:** HTTP 402 (credits exhausted) and 403 (plan-gated) stop the run immediately with a clear message and no retries. | Mock 402 and 403 responses; assert exceptions raised immediately with exact clear error messages. | `tests/test_crustdata_client.py::test_client_402_and_403_stop` |
| 4 | **Key Security & Git-ignore:** Read Crustdata key only from local environment variable (`CRUSTDATA_API_KEY`). Confirm files holding keys are git-ignored. Never print, commit, or log the key. | Test key loading, git-ignore check verification, and log masking checks (`***`). | `tests/test_crustdata_client.py::test_key_security_and_masking` |
| 5 | **Credit Budget Guard:** Before live call, check `GET /account/credits`; ensure budget strictly under 200 credits for the run. | Credit calculation test ensuring discovery + verification stays well within budget (< 200 credits). | `tests/test_crustdata_client.py::test_credit_guard` |
| 6 | **Discovery (Step 2):** Ranked search (`search.query`) first, location filters as hard limits, `company_autocomplete` before any industry filter, fallback to filters-only. Single window up to 100 results, no paging. | Discovery unit tests with mocked/fixture Crustdata API responses testing ranked search, location limits, and autocomplete resolution. | `tests/test_crustdata_discovery.py::test_discovery_ranked_and_autocomplete` |
| 7 | **Verification (Step 3):** `company_identify` first (free), then `company_enrich` (2 credits) for `headcount`, `locations`, and `basic_info.description`. Never request headcount/locations on identify. | Test verifying multi-stage verification flow and asserting identify never requests plan-gated fields. | `tests/test_crustdata_verification.py::test_verification_identify_then_enrich` |
| 8 | **Product-line Check:** Read `basic_info.description` on enrich. If empty or absent, mark status as `HUMAN_OR_SIMULATED`. If populated, mark as `CONFIRMED`. | Test with enriched records with populated and empty descriptions. | `tests/test_crustdata_verification.py::test_product_line_status` |
| 9 | **Dedupe (Step 4):** One record per company, matching by primary domain and normalized company name, with match confidence score. | Test with duplicate candidate companies (e.g. slight name variations, identical domain). | `tests/test_crustdata_dedupe.py::test_deduplication` |
| 10 | **Screen Display & Citations (Option C):** Screens show display labels (`Supplier 1`, ...) and citations only ("Source: Crustdata", endpoint, field). Real names and values stay in `*_internal` fields for log/policy only. | Test verifying screen output formatting contains no company values or real names. | `tests/test_crustdata_screen.py::test_screen_data_option_c` |
| 11 | **Demo Citation Script:** Standalone citation script demonstrating Option C formatted output for demo/video. | Run citation script against fixtures, validating compliant output. | `src/discovery/demo_citation.py` / `tests/test_demo_citation.py` |
| 12 | **Offline / Fixture Support:** Complete run works out of the box using realistic industrial sensor supplier fixtures without any network calls. | End-to-end fixture execution test across steps 2-4. | `tests/test_crustdata_fixtures.py::test_fixture_run_end_to_end` |

---

## 2. Architecture & File Layout
Files owned by Person 2:
- `src/crustdata/`:
  - `client.py`: HTTP client, headers, backoff for 429, stop on 402/403, key security & masking.
  - `models.py`: Internal data models matching contract in section 6.
  - `credits.py`: Account credit checking and budget calculations.
- `src/discovery/`:
  - `candidate_search.py`: Step 2 ranked search, location hard limits, autocomplete before industry filter.
  - `verify.py`: Step 3 identify (free) -> enrich (2 credits) for headcount, locations, description.
  - `dedupe.py`: Step 4 deduplication with match confidence.
  - `fixtures.py` / `fixtures/`: Realistic fixture candidates and enrichments for industrial temperature sensors.
  - `service.py`: Orchestrator for steps 2, 3, 4 with screen-safe display formatting.
  - `demo_citation.py`: Demo citation script for Option C compliance.
- `tests/`:
  - `test_crustdata_client.py`
  - `test_crustdata_discovery.py`
  - `test_crustdata_verification.py`
  - `test_crustdata_dedupe.py`
  - `test_crustdata_screen.py`
  - `test_crustdata_fixtures.py`
  - `test_demo_citation.py`

---

## 3. Progress Log & Test Verification
- Initialized branch `feat/issue-7-discovery`.
- Formulated acceptance checks from issue #7 and master handoff sections 4, 5, 6, 7, 8, 12.
- Implemented Crustdata client with headers, 429 backoff, 402/403 immediate stopping, and key protection (`src/crustdata/client.py`).
- Implemented credit cost estimation and `CreditGuard` enforcing strictly < 200 credits budget (`src/crustdata/credits.py`).
- Added realistic Industrial Temperature Sensor fixtures (`src/discovery/fixtures.py`) covering candidates, identify mappings, enrich responses with descriptions, empty descriptions, and dedupe pairs.
- Implemented Step 2 discovery (`src/discovery/candidate_search.py`) with ranked `search.query` first, location hard limits, autocomplete before industry filter, and fallback.
- Implemented Step 3 verification (`src/discovery/verify.py`) with free identify first, enrich for headcount and locations, and product line status (`CONFIRMED` or `HUMAN_OR_SIMULATED`).
- Implemented Step 4 deduplication (`src/discovery/dedupe.py`) with domain normalization and similarity-based merging.
- Implemented Option C display formatter and internal audit logger (`src/discovery/service.py`).
- Created demo citation runner (`demo_citations.py` and `src/discovery/demo_citation.py`).

---

## 4. Owner Review (Bratadeep) Feedback & Resolutions
Addressing the four feedback items from issue #7 review:

1. **Errors stop the run (`src/discovery/verify.py` & `src/discovery/candidate_search.py`):**
   - Re-raised `CrustdataCreditsExhaustedError` (402), `CrustdataPlanGatedError` (403), and `CrustdataRateLimitError` (429) across candidate identify, enrich, search, and autocomplete operations.
   - Added unit test `test_verify_all_stops_immediately_on_402_called_only_once` asserting that `company_identify` is called exactly once when a 402 is raised and loop stops immediately.
   - Added unit test `test_verify_all_stops_immediately_on_403` asserting immediate halt on plan-gated errors.

2. **Credit guard enforced on live path (`src/discovery/service.py`):**
   - Live execution path invokes `check_account_credits` and pre-checks projected spend against balance and safety budget (< 200 credits).
   - Fails closed (`CrustdataCreditsExhaustedError`) before making any network calls if credits are insufficient or cannot be queried.
   - Added unit tests `test_live_pipeline_fails_closed_when_credits_insufficient` and `test_live_pipeline_fails_closed_when_credits_check_fails`.

3. **Screen privacy on demo script (`src/discovery/demo_citation.py`):**
   - Removed stdout printing of internal log. The internal record is written strictly to `discovery_internal_audit.log` for policy consumption.
   - Verified that screen output contains ONLY neutral display labels (`Supplier 1`, ...) and citations, with zero company names or metrics.

4. **Document demo command:**
   - Standard execution command is plain: `python demo_citations.py`.
   - Updated `demo_citations.py` with dynamic `sys.path` insertion to guarantee robust execution across all environments.

- All 32 unit tests passing:
  `python -m unittest discover -s tests -p "crustdata*.py"`
