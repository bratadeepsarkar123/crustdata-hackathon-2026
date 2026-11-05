# ContextCon 04: Person 2 Handoff (Discovery & Crustdata)

**To:** `@bratadeepsarkar123` (Person 1 / Integrator)  
**Cc:** `@debugat2am` (Person 3 / Quotes & WhatsApp)  
**From:** `@AdityaChittora` (Person 2 / Discovery & Crustdata)  
**Date:** 6 November 2026  
**Branch:** `feat/issue-7-discovery`  
**Pull Request:** [#9](https://github.com/bratadeepsarkar123/crustdata-hackathon-2026/pull/9)  
**Status:** **READY FOR INTEGRATION (IP1 -> IP2)**

---

## 1. Executive Summary

Person 2's assigned scope (Steps 2, 3, and 4) is **fully implemented, tested, and ready for integration**:
1. **Step 2 (Find Candidates):** Ranked `search.query` first, location filters applied as hard limits, `company_autocomplete` executed before industry filtering, single window up to 100 results, and filters-only fallback.
2. **Step 3 (Verify):** Two-stage verification calling `POST /company/identify` (free) first, then `POST /company/enrich` (2 credits) for `headcount`, `locations`, and `basic_info.description`. Includes an explicit code guard preventing identify from requesting plan-gated fields. Marks product line as `CONFIRMED` (description present) or `HUMAN_OR_SIMULATED` (description empty).
3. **Step 4 (Dedupe):** Normalizes domains and company names, calculates string & token similarity, merges duplicate entities, combines citations, and computes match confidence.
4. **Display Rule (Option C):** Enforces neutral labels (`Supplier 1`, `Supplier 2`, ...) and citations only (*"Source: Crustdata (endpoint, field)"*). Real names and metrics are strictly contained within `_internal` fields.
5. **Security & Credits:** Zero API keys committed or printed. Key read exclusively from environment (`CRUSTDATA_API_KEY`) with git-ignore validation. Live calls disabled by default (`allow_live=False`); `CreditGuard` ensures the live run stays strictly under 200 credits (estimated run is ~10.60 credits).

---

## 2. Shared Interface Contract (How Person 1 & Person 3 Consume It)

### Pipeline Entry Point
```python
from src.discovery.service import run_discovery_pipeline, format_screen_display, format_internal_log

# 1. Run discovery and verification (offline on fixtures by default)
suppliers = run_discovery_pipeline(
    request={
        "item": "industrial temperature sensors",
        "quantity": 500,
        "budget": 25000,
        "currency": "USD",
        "deadline_days": 14,
        "region": "India",
        "missing_fields": [],
    },
    use_fixtures=True,  # Set to False once @bratadeepsarkar123 approves live IP3 run
)

# 2. For the UI / screen display / demo video (Option C strictly enforced):
screen_text = format_screen_display(suppliers)
print(screen_text)

# 3. For downstream policy checks (Person 3) and internal audit logs:
internal_log = format_internal_log(suppliers)
```

### Output Data Shape (Matches Section 6 Contract)
Each supplier in `suppliers` is a dictionary conforming exactly to `MASTER-HANDOFF-supplier.md` Section 6:
```json
{
  "display_label": "Supplier 1",
  "name_internal": "Tempsens Instruments",
  "primary_domain": "tempsens.com",
  "year_founded": 1976,
  "headquarters_internal": "Udaipur, Rajasthan, India",
  "headcount_total_internal": 650,
  "industry": "Sensors & Measuring Instruments",
  "product_line_status": "CONFIRMED",
  "sources": [
    { "field": "name", "endpoint": "/company/search" },
    { "field": "primary_domain", "endpoint": "/company/search" },
    { "field": "headcount", "endpoint": "/company/enrich" },
    { "field": "locations", "endpoint": "/company/enrich" },
    { "field": "basic_info.description", "endpoint": "/company/enrich" }
  ],
  "confidence": 0.98
}
```

> **For Person 3 (`debugat2am`):** You can read `headcount_total_internal` and `headquarters_internal` for your policy evaluation rules, but only use `display_label` and the `sources` citations on any screen/quote display.

---

## 3. Files Delivered

All files are strictly within Person 2's ownership scope:

| Path | Purpose |
|---|---|
| `src/crustdata/client.py` | API client with headers, 429 backoff (`Retry-After`), 402/403 immediate stop, and key masking. |
| `src/crustdata/credits.py` | `GET /account/credits` checker, batch cost estimation, and `CreditGuard` (< 200 budget). |
| `src/crustdata/exceptions.py` | Custom error classes for clean diagnostics. |
| `src/discovery/fixtures.py` | Realistic Industrial Temperature Sensor supplier fixtures (India & global). |
| `src/discovery/candidate_search.py` | Step 2 ranked search, location hard limits, and autocomplete. |
| `src/discovery/verify.py` | Step 3 identify first (free), then enrich (2 credits), product line verification. |
| `src/discovery/dedupe.py` | Step 4 domain and company name normalization, similarity scoring, and deduplication. |
| `src/discovery/service.py` | Pipeline orchestrator and Option C display/log formatters. |
| `src/discovery/demo_citation.py` | Standalone citation verification runner for the demo. |
| `demo_citations.py` | Repo-root shortcut to run the demo citation script. |
| `tests/crustdata*.py` | 7 test files (28 tests total) covering all acceptance criteria. |
| `NOTES.md` | Living engineering notes documenting checks, architecture, and verification. |

---

## 4. Verification and Acceptance Checks

### Test Suite Execution
Run all Person 2 tests with:
```powershell
python -m unittest discover -s tests -p "crustdata*.py"
```
**Result:** 28 tests ran, 0 failures, 0 errors in 0.011s.

### Demo Citation Script Execution
Run the demo citation script with:
```powershell
python demo_citations.py
```
**Result:** Returns 0; displays Option C compliant screen output with citations for every fact and zero leaked real names or values.

---

## 5. Next Steps for Person 1 (`bratadeepsarkar123`)

1. **Pull and test branch:**
   ```bash
   git fetch origin
   git checkout feat/issue-7-discovery
   python -m unittest discover -s tests -p "crustdata*.py"
   python demo_citations.py
   ```
2. **Review & Merge Draft PR #9** into `main` for integration milestone IP1 / IP2.
3. **Live Run (IP3):** When ready for the live Crustdata run, set `CRUSTDATA_API_KEY` in your environment and notify Person 2 (`@AdityaChittora`). We will verify credits via `GET /account/credits` before triggering the live run.
