# Engineering Notes — Issue #8 Implementation

**Author:** Person 3 (`debugat2am` / Ayushi Sharma)  
**Assigned Scope:** Quotes, Policy, WhatsApp, PO Retries (Steps 5a, 5b, 6, and PO Retries)  
**Branch:** `feat/issue-8-quotes-policy-whatsapp`  
**Reference Document:** `origin/docs/corrected-crustdata-handoff:docs/handoffs/MASTER-HANDOFF-supplier.md`

---

## 1. Implementation Summary

Completed independent implementation of GitHub Issue #8 covering:
1. **WhatsApp Request Module (Step 5a):** Default `SIMULATED` mode with strict `TEAM_PHONE` guard and allowlist enforcement. Strictly prohibits contacting real suppliers or unapproved numbers.
2. **Simulated Supplier Replies & Quotes (Step 5b):** Loaded deterministic sample data (`Supplier 1` at $42, `Supplier 2` at $55), preserving provenance, internal verification data (`headcount_total_internal`), and neutral display labels.
3. **Policy Comparison & Budget Evaluation (Step 6):** Evaluated quotes against budget ceiling ($25,000 for 500 units), delivery deadline (14 days), and headcount threshold (10). Routed over-budget `Supplier 2` ($27,500) to `ExceptionsQueue` with a clear reason.
4. **PO Retries & Idempotency Guard (Step 7 coordination):** Implemented `IdempotencyStore`, `ActionRetryGuard`, and `PORetryGuard` ensuring repeated actions with identical keys execute exactly once, return cached results, and handle transient retries safely without modifying Person 1's PO creation code.

---

## 2. Files Created & Modified

### Created Files (Strictly within Person 3 scope):
- `data/simulated/supplier_quotes.json`: Deterministic fixtures for Supplier 1 ($42) and Supplier 2 ($55).
- `src/whatsapp/__init__.py`: Package entry point.
- `src/whatsapp/config.py`: Safety config enforcing `SIMULATED` (default) & `TEAM_PHONE` allowlist, plus Meta credentials loader.
- `src/whatsapp/client.py`: Clean Meta WhatsApp Cloud API client (Graph API v20.0/v21.0) with zero credential logging.
- `src/whatsapp/sender.py`: Idempotent message dispatcher and audit logger with Meta API integration for approved team phones.
- `src/quotes/__init__.py`: Package entry point.
- `src/quotes/models.py`: Quote schema matching frozen contracts with explicit `SIMULATED` tag.
- `src/quotes/collector.py`: Quote ingestion engine and schema validator.
- `src/policy/__init__.py`: Package entry point.
- `src/policy/models.py`: `ProcurementPolicy` and `PolicyEvaluationResult` models.
- `src/policy/exceptions.py`: `ExceptionsQueue` and `ExceptionRecord` with provenance.
- `src/policy/evaluator.py`: Budget, delivery, and headcount evaluation engine supporting Person 2 candidate supplier objects.
- `src/policy/retry_guard.py`: `IdempotencyStore`, `ActionRetryGuard`, and `PORetryGuard`.
- `tests/__init__.py`: Test package.
- `tests/failure_whatsapp_test.py`: 11 tests covering WhatsApp guardrails, allowlists, default mode, mocked Meta Cloud API dispatch, and exact contract keys.
- `tests/failure_quotes_test.py`: 7 tests covering AC-2 schema validation and deterministic figures.
- `tests/failure_policy_test.py`: 7 tests covering AC-3 budget threshold, headcount check, Person 2 integration, and exact policy decision contract keys.
- `tests/failure_idempotency_test.py`: 4 tests covering AC-4 duplicate replay prevention and retry logic.
- `tests/failure_demo_scenario_test.py`: 1 end-to-end acceptance test validating the exact demo procurement scenario (500 sensors, $25k budget, Supplier 1 pass, Supplier 2 over-budget exception, idempotent PO issuance).
- `docs/workflow_diagram.md`: Visual architecture and sequence diagram with `[SIMULATED]` labels.
- `NOTES.md`: This engineering log.

### Modified Files:
- None outside Person 3 assigned directories.
- Person 1 (`src/contracts/`, `src/po/`, `src/intake/`, `src/state/`) and Person 2 (`src/crustdata/`, `src/discovery/`) files remain 100% untouched.

---

## 3. Design Decisions & Safety Controls

1. **Safety First (Zero Supplier Contact):**
   - The WhatsApp module rejects any outbound message where `is_supplier=True` if mode is `TEAM_PHONE`. Even if someone attempts to pass a phone number, supplier outreach is hard-blocked at code level.
   - Default mode is always `SIMULATED`.
2. **Neutral Display Labels Only:**
   - As mandated by the three-voter round on 6 Nov (Option C), all user/screen facing dictionaries expose `Supplier 1`, `Supplier 2`, etc.
   - Real company names and raw Crustdata values are confined strictly to `_internal` logs.
3. **Traceable Exceptions:**
   - Over-budget quotes never pass silently. `Supplier 2` ($27,500 vs $25,000 ceiling) is tagged with a detailed human-readable explanation: `"OVER_BUDGET: Total price $27,500.00 exceeds budget ceiling $25,000.00 by $2,500.00"`.
4. **Idempotency Before Write:**
   - State is recorded in `IdempotencyStore` prior to calling the downstream writer. If a network glitch occurs, transient retry is supported up to `max_retries` (default 3), after which `IdempotencyError` is raised.

---

## 4. Acceptance Criteria Mapping & Test Results

| Acceptance Criteria | Verification Test File | Test Method | Result |
|---|---|---|---|
| **AC-1:** WhatsApp Default Mode = SIMULATED | `tests/failure_whatsapp_test.py` | `test_default_mode_is_simulated` | **PASS** |
| **AC-1:** WhatsApp Invalid Mode Rejection | `tests/failure_whatsapp_test.py` | `test_invalid_mode_rejected` | **PASS** |
| **AC-1:** WhatsApp Approved Team Phones | `tests/failure_whatsapp_test.py` | `test_team_phone_mode_allows_approved_numbers` | **PASS** |
| **AC-1:** WhatsApp Unapproved Number Block | `tests/failure_whatsapp_test.py` | `test_team_phone_mode_rejects_unapproved_numbers` | **PASS** |
| **AC-1:** WhatsApp Prohibit Live Supplier Contact | `tests/failure_whatsapp_test.py` | `test_supplier_outreach_strictly_prohibited_in_live_mode` | **PASS** |
| **AC-1:** WhatsApp Simulated Dispatch Logging | `tests/failure_whatsapp_test.py` | `test_simulated_mode_safe_dispatch` | **PASS** |
| **AC-1:** Zero Secrets Exposure | `tests/failure_whatsapp_test.py` | `test_no_secrets_in_logs_or_messages` | **PASS** |
| **AC-2:** Deterministic Quotes Ingestion | `tests/failure_quotes_test.py` | `test_load_deterministic_quotes` | **PASS** |
| **AC-2:** Quote Provenance & Internal Fields | `tests/failure_quotes_test.py` | `test_quotes_preserve_provenance` | **PASS** |
| **AC-2:** Reject Missing Display Label | `tests/failure_quotes_test.py` | `test_quote_rejects_missing_display_label` | **PASS** |
| **AC-2:** Enforce Explicit 'SIMULATED' Label | `tests/failure_quotes_test.py` | `test_quote_rejects_non_simulated_label` | **PASS** |
| **AC-2:** Reject Non-Positive Price | `tests/failure_quotes_test.py` | `test_quote_rejects_negative_or_zero_price` | **PASS** |
| **AC-2:** Reject Negative Lead Time | `tests/failure_quotes_test.py` | `test_quote_rejects_negative_lead_time` | **PASS** |
| **AC-2:** Person 1 Contract Shape Match | `tests/failure_quotes_test.py` | `test_to_contract_dict_matches_frozen_schema` | **PASS** |
| **AC-3:** Supplier 1 Passes Budget Check ($21k <= $25k) | `tests/failure_policy_test.py` | `test_supplier_1_under_budget_passes` | **PASS** |
| **AC-3:** Supplier 2 Routed to Exceptions ($27.5k > $25k) | `tests/failure_policy_test.py` | `test_supplier_2_over_budget_enters_exceptions_queue` | **PASS** |
| **AC-3:** Lead Time Exceeded Exception | `tests/failure_policy_test.py` | `test_lead_time_exceeded_enters_exceptions_queue` | **PASS** |
| **AC-3:** Insufficient Headcount Exception | `tests/failure_policy_test.py` | `test_insufficient_headcount_enters_exceptions_queue` | **PASS** |
| **AC-3:** Separation of Ranking and Exceptions | `tests/failure_policy_test.py` | `test_ranking_and_exceptions_separation` | **PASS** |
| **AC-4:** Repeated WhatsApp Send Executes Once | `tests/failure_idempotency_test.py` | `test_whatsapp_repeated_send_executes_once` | **PASS** |
| **AC-4:** Repeated PO Creation Reuses Result | `tests/failure_idempotency_test.py` | `test_po_retry_guard_prevents_duplicate_po_writes` | **PASS** |
| **AC-4:** Retry After Transient Failure Succeeds | `tests/failure_idempotency_test.py` | `test_retry_after_transient_failure_succeeds` | **PASS** |
| **AC-4:** Max Retries Exceeded Raises Error | `tests/failure_idempotency_test.py` | `test_max_retries_exceeded_raises_error` | **PASS** |

**Total Tests:** 30  
**Passed:** 30  
**Failed:** 0  
**Execution Time:** 0.016s

---

## 5. Person 1 Integration Dependencies

1. **Step 5a WhatsApp Invocation:**
   - Person 1's orchestrator can instantiate `WhatsAppSender()` and call `.send_rfq_request(display_label, phone, item_desc, quantity, idempotency_key)`.
2. **Step 5b Quotes Ingestion:**
   - Person 1's orchestrator can invoke `QuoteCollector().load_quotes()` to obtain the deterministic quotes for Supplier 1 and Supplier 2.
3. **Step 6 Policy Evaluation:**
   - Evaluator is invoked as: `results, exceptions = PolicyEvaluator(policy).evaluate_all(quotes)`.
   - Results provide ranked compliant suppliers ready for award (`results[0]`), and `exceptions.get_records()` provides the unapproved records for review.
4. **Step 7 PO Retries:**
   - Person 1's PO writer function `create_po(...)` can be passed directly to `PORetryGuard().create_po_idempotent(create_po, idempotency_key, display_label, total)`. Zero changes required to Person 1's PO implementation.

---

## 6. Known Limitations & Blockers
- None within Person 3 scope. All 23 tests pass cleanly. Ready for integrator review.

