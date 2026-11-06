# Supplier Sourcing & Procurement Agent — Workflow Architecture

**ContextCon 04 Hackathon**  
**Role:** Person 3 (`debugat2am`) — Quotes, Policy, PO Retries  
**Scope:** Steps 5a, 5b, 6, and PO retry / idempotency guard coordination (Step 7).

---

## 1. End-to-End Pipeline & Simulation Boundaries

```mermaid
flowchart TD
    subgraph Step1_4["Upstream Pipeline (Person 1 & Person 2)"]
        Req["Step 1: Purchase Request Intake<br/><i>(500 Sensors, $25k Budget, 14d Delivery)</i><br/><b>[REAL]</b>"] --> CD["Steps 2-4: Crustdata Discovery & Verification<br/><i>(Search, Identify, Enrich Headcount/Location)</i><br/><b>[REAL]</b>"]
        CD --> VSupp["Verified Candidate Suppliers<br/><i>(Display Labels: Supplier 1, Supplier 2)</i><br/><b>[REAL]</b>"]
    end

    subgraph Step5["Step 5: Quote Collection (Person 3)"]
        VSupp --> Quote_Load["Step 5b: Load Deterministic Quotes<br/><i>(data/simulated/supplier_quotes.json)</i><br/><b>[SIMULATED]</b>"]
        
        Quote_Load --> Q1["Supplier 1 Quote:<br/>$42/unit * 500 = $21,000<br/>Lead Time: 12d<br/><b>[SIMULATED]</b>"]
        Quote_Load --> Q2["Supplier 2 Quote:<br/>$55/unit * 500 = $27,500<br/>Lead Time: 12d<br/><b>[SIMULATED]</b>"]
    end

    subgraph Step6["Step 6: Policy Comparison & Budget Check (Person 3)"]
        Q1 --> PolEval["Policy Evaluator<br/><i>(Budget <= $25,000, Delivery <= 14d)</i><br/><b>[REAL LOGIC on SIMULATED DATA]</b>"]
        Q2 --> PolEval
        
        PolEval -- "Total $21,000 <= $25,000 (Compliant)" --> Rank["Rank 1: Supplier 1<br/>Approved for Award<br/><b>[APPROVED]</b>"]
        PolEval -- "Total $27,500 > $25,000 (Over Budget)" --> ExcQueue["Exceptions Queue:<br/>Supplier 2 Routed with Reason:<br/>'total 27500 is over the budget of 25000'<br/><b>[HUMAN-IN-THE-LOOP EXCEPTION]</b>"]
    end

    subgraph Step7["Step 7: PO Creation & Retries (Person 1 + Person 3 Guard)"]
        Rank --> IdempGuard{"Idempotency Store Check<br/><i>(Key: po_writer intent)</i>"}
        IdempGuard -- "Key Not Seen" --> CreatePO["Call Person 1 PO Writer<br/>Atomically write immutable PO<br/><b>[SIMULATED PO]</b>"]
        IdempGuard -- "Key Already Succeeded" --> CachedPO["Return Existing Record<br/><i>(Zero Duplicate PO Creation)</i><br/><b>[IDEMPOTENT REPLAY]</b>"]
    end
```

---

## 2. Sequence Diagram: Quotes, Policy Evaluation & Idempotent Retries

```mermaid
sequenceDiagram
    autonumber
    participant Orch as Person 1 Orchestrator
    participant QC as QuoteCollector (Step 5b)
    participant PE as PolicyEvaluator (Step 6)
    participant PO as Person 1 PO Writer (Step 7)

    Note over Orch, QC: Step 5b Quote Ingestion
    Orch->>QC: loadSimulatedQuotes()
    QC-->>Orch: [Supplier 1 ($42/unit, 12d), Supplier 2 ($55/unit, 12d)] [SIMULATED]

    Note over Orch, PE: Step 6 Policy Evaluation
    Orch->>PE: evaluateQuotesPolicy(request, quotes)
    PE-->>Orch: Supplier 1 -> Approved (Rank 1, Total $21,000 <= $25,000)
    PE-->>Orch: Supplier 2 -> Exceptions Queue (Over Budget: $27,500 > $25,000)

    Note over Orch, PO: Step 7 Idempotent PO Creation
    Orch->>PO: writeVendorAndPo(inputs)
    PO-->>Orch: PO-2026-0001 (status: CREATED) [SIMULATED]

    Note over Orch, PO: Accidental Duplicate PO Request on Retry
    Orch->>PO: writeVendorAndPo(inputs)
    Note over PO: Key exists in idempotency store. Action not re-executed!
    PO-->>Orch: Cached PO-2026-0001 (status: EXISTS) [SIMULATED]
```

---

## 3. Strict Truthfulness & Simulation Disclaimers

1. **Quotes:** All quotations, pricing (\$42 / \$55), and delivery timelines are deterministic synthetic fixtures from `data/simulated/supplier_quotes.json` and carry the mandatory `"label": "SIMULATED"`.
2. **Purchase Orders:** All PO numbers (e.g. `PO-2026-XXXX`) and vendor onboarding records are synthetic demonstrations for ContextCon 04. No external ERP or cellular network was contacted.
