# Supplier Sourcing & Procurement Agent — Workflow Architecture

**ContextCon 04 Hackathon**  
**Role:** Person 3 (`debugat2am`) — Quotes, Policy, WhatsApp, PO Retries  
**Scope:** Steps 5a, 5b, 6, and PO retry / idempotency guard coordination (Step 7).

---

## 1. End-to-End Pipeline & Simulation Boundaries

```mermaid
flowchart TD
    subgraph Step1_4["Upstream Pipeline (Person 1 & Person 2)"]
        Req["Step 1: Purchase Request Intake<br/><i>(500 Sensors, $25k Budget, 14d Delivery)</i><br/><b>[REAL]</b>"] --> CD["Steps 2-4: Crustdata Discovery & Verification<br/><i>(Search, Identify, Enrich Headcount/Location)</i><br/><b>[REAL]</b>"]
        CD --> VSupp["Verified Candidate Suppliers<br/><i>(Display Labels: Supplier 1, Supplier 2)</i><br/><b>[REAL]</b>"]
    end

    subgraph Step5["Step 5: WhatsApp RFQ & Quote Collection (Person 3)"]
        VSupp --> WA_Guard{"WhatsApp Guard & Mode Check<br/><i>(SIMULATED or TEAM_PHONE only)</i>"}
        WA_Guard -- "SIMULATED (Default)" --> WA_SimLog["Log Outbound RFQ to Audit Log<br/><b>[SIMULATED]</b>"]
        WA_Guard -- "TEAM_PHONE" --> WA_TeamCheck{"Phone in Allowlist?"}
        WA_TeamCheck -- "Yes" --> WA_RealTeam["Send to Teammate Test Phone<br/><b>[REAL - Team Only]</b>"]
        WA_TeamCheck -- "No / Real Supplier" --> WA_Block["Block Call & Raise SecurityError<br/><b>[SECURITY REJECTION]</b>"]
        
        WA_SimLog --> Quote_Load["Step 5b: Load Deterministic Quotes<br/><i>(data/simulated/supplier_quotes.json)</i><br/><b>[SIMULATED]</b>"]
        WA_RealTeam --> Quote_Load
        
        Quote_Load --> Q1["Supplier 1 Quote:<br/>$42/unit * 500 = $21,000<br/>Lead Time: 10d, Net 30<br/><b>[SIMULATED]</b>"]
        Quote_Load --> Q2["Supplier 2 Quote:<br/>$55/unit * 500 = $27,500<br/>Lead Time: 12d, Net 30<br/><b>[SIMULATED]</b>"]
    end

    subgraph Step6["Step 6: Policy Comparison & Budget Check (Person 3)"]
        Q1 --> PolEval["Policy Evaluator<br/><i>(Budget <= $25,000, Delivery <= 14d, Headcount >= 10)</i><br/><b>[REAL LOGIC on SIMULATED DATA]</b>"]
        Q2 --> PolEval
        
        PolEval -- "Total $21,000 <= $25,000 (Compliant)" --> Rank["Rank 1: Supplier 1<br/>Approved for Award<br/><b>[APPROVED]</b>"]
        PolEval -- "Total $27,500 > $25,000 (Over Budget)" --> ExcQueue["Exceptions Queue:<br/>Supplier 2 Routed with Reason:<br/>'OVER_BUDGET: $27,500 exceeds $25,000'<br/><b>[HUMAN-IN-THE-LOOP EXCEPTION]</b>"]
    end

    subgraph Step7["Step 7: PO Creation & Retries (Person 1 + Person 3 Guard)"]
        Rank --> IdempGuard{"PORetryGuard Check<br/><i>(Key: VEND-ONBOARD-...)</i>"}
        IdempGuard -- "Key Not Seen" --> CreatePO["Call Person 1 PO Factory<br/>Record Key in Idempotency Store<br/><b>[SIMULATED PO]</b>"]
        IdempGuard -- "Key Already Succeeded" --> CachedPO["Return Cached PO<br/><i>(Zero Duplicate PO Creation)</i><br/><b>[IDEMPOTENT REPLAY]</b>"]
        IdempGuard -- "Transient Failure" --> RetryPO["Retry with Backoff<br/><i>(Up to Max Retries)</i><br/><b>[TRANSIENT RESILIENCE]</b>"]
    end
```

---

## 2. Sequence Diagram: WhatsApp Dispatch, Policy Evaluation & Idempotent Retries

```mermaid
sequenceDiagram
    autonumber
    participant Orch as Person 1 Orchestrator
    participant WA as WhatsAppSender (Step 5a)
    participant QC as QuoteCollector (Step 5b)
    participant PE as PolicyEvaluator (Step 6)
    participant RG as PORetryGuard (Step 7)
    participant PO as Person 1 PO Writer

    Note over Orch, WA: Mode = SIMULATED (Default)
    Orch->>WA: send_rfq_request(Supplier 1, idempotency_key="key-01")
    WA-->>Orch: Record logged with [SIMULATED] label (Replayed: false)

    Note over Orch, WA: Duplicate WhatsApp Send Attempt
    Orch->>WA: send_rfq_request(Supplier 1, idempotency_key="key-01")
    WA-->>Orch: Returns cached record (Replayed: true, send_count: 1)

    Note over Orch, QC: Step 5b Quote Ingestion
    Orch->>QC: load_quotes()
    QC-->>Orch: [Supplier 1 ($21,000, 10d), Supplier 2 ($27,500, 12d)] [SIMULATED]

    Note over Orch, PE: Step 6 Policy Evaluation
    Orch->>PE: evaluate_all([Supplier 1, Supplier 2])
    PE-->>Orch: Supplier 1 -> Compliant (Rank 1)
    PE-->>Orch: Supplier 2 -> Routed to ExceptionsQueue ("OVER_BUDGET: $27,500 > $25,000")

    Note over Orch, PO: Step 7 Idempotent PO Creation
    Orch->>RG: create_po_idempotent(mock_person_1_po_create, key="vend-po-01")
    RG->>PO: execute PO creation (1st time)
    PO-->>RG: PO-2026-0001-SIMULATED
    RG-->>Orch: PO-2026-0001-SIMULATED

    Note over Orch, PO: Accidental Duplicate PO Request on Retry
    Orch->>RG: create_po_idempotent(mock_person_1_po_create, key="vend-po-01")
    Note over RG: Key exists in store with status SUCCESS. Action not re-executed!
    RG-->>Orch: Cached PO-2026-0001-SIMULATED (idempotency_replayed: true)
```

---

## 3. Strict Truthfulness & Simulation Disclaimers

1. **WhatsApp Messages:** All supplier outreach is strictly **SIMULATED**. Only test communication between designated team phones is permitted under `TEAM_PHONE` mode.
2. **Quotes:** All quotations, pricing ($42 / $55), and delivery timelines are deterministic synthetic fixtures from `data/simulated/supplier_quotes.json` and carry the mandatory `"label": "SIMULATED"`.
3. **Purchase Orders:** All PO numbers (e.g. `PO-2026-0001-SIMULATED`) and vendor onboarding records are synthetic demonstrations for ContextCon 04. No external ERP or cellular network was contacted.

