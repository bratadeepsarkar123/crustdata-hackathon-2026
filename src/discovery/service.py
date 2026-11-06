"""Discovery & Verification orchestrator (Steps 2 to 4) and Option C screen formatter."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.crustdata.client import CrustdataClient
from src.crustdata.credits import (
    CreditGuard,
    calculate_batch_cost,
    check_account_credits,
    MAX_RUN_CREDIT_BUDGET,
)
from src.crustdata.exceptions import (
    CrustdataBudgetExceededError,
    CrustdataCreditsExhaustedError,
)
from .candidate_search import search_candidate_suppliers
from .verify import verify_all_candidates
from .dedupe import dedupe_candidates

logger = logging.getLogger("discovery.service")


def run_discovery_pipeline(
    request: Dict[str, Any],
    client: Optional[CrustdataClient] = None,
    use_fixtures: bool = True,
    industry_filter: Optional[str] = None,
    credit_guard: Optional[CreditGuard] = None,
    max_candidates_to_verify: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Execute complete Discovery pipeline (Steps 2, 3, 4).

    Steps:
    2. Find candidates (ranked search.query + location limits + autocomplete)
    3. Verify each company (identify first, then enrich by ID)
    4. Dedupe candidates (domain and name similarity)
    Assigns neutral display labels ("Supplier 1", "Supplier 2", ...) per Option C.
    """
    logger.info("Starting supplier discovery for item: %s", request.get("item"))

    guard = credit_guard
    # Live path guard: verify credit balance and enforce CreditGuard before any live call
    if not use_fixtures and client and client.allow_live and guard is None:
        estimated_cost = calculate_batch_cost(
            search_results_count=100,
            identify_count=10,
            enrich_count=5,
            autocomplete_count=1 if industry_filter else 0,
        )
        logger.info("Projected live discovery cost: %.2f credits", estimated_cost)

        try:
            available_credits = check_account_credits(client)
            logger.info("Available Crustdata credits: %.2f", available_credits)
        except Exception as exc:
            logger.error("Failed to check Crustdata account credits: %s. Failing closed.", exc)
            raise CrustdataCreditsExhaustedError(
                f"Credit pre-flight check failed: Unable to verify account credits ({exc}). "
                "Failing closed before making any live calls."
            ) from exc

        if available_credits < estimated_cost:
            raise CrustdataCreditsExhaustedError(
                f"Crustdata credits insufficient: Available ({available_credits:.2f}) < "
                f"Estimated run cost ({estimated_cost:.2f}). Failing closed."
            )

        guard = CreditGuard(max_budget=available_credits)
        guard.estimate_and_check(estimated_cost)

    # Step 2: Search candidate suppliers
    raw_candidates = search_candidate_suppliers(
        request=request,
        client=client,
        use_fixtures=use_fixtures,
        industry_filter=industry_filter,
        credit_guard=guard,
    )
    logger.info("Found %d candidate suppliers in Step 2", len(raw_candidates))

    candidates_to_verify = raw_candidates
    if max_candidates_to_verify is not None:
        candidates_to_verify = raw_candidates[:max_candidates_to_verify]
    elif not use_fixtures:
        candidates_to_verify = raw_candidates[:5]

    # Step 3: Verify each company
    verified_candidates = verify_all_candidates(
        candidates=candidates_to_verify,
        client=client,
        use_fixtures=use_fixtures,
        credit_guard=guard,
    )
    logger.info("Verified %d candidates in Step 3", len(verified_candidates))

    # Step 4: Dedupe candidates
    deduped_suppliers = dedupe_candidates(verified_candidates)
    logger.info("Retained %d unique suppliers after Step 4 deduplication", len(deduped_suppliers))

    # Format exactly to Section 6 / PR #10 contract shape (SUPPLIER_KEYS)
    SUPPLIER_KEYS = [
        "display_label",
        "name_internal",
        "primary_domain",
        "year_founded",
        "headquarters_internal",
        "headcount_total_internal",
        "industry",
        "product_line_status",
        "sources",
        "confidence",
    ]

    clean_suppliers = []
    for idx, supplier in enumerate(deduped_suppliers, start=1):
        record = {
            "display_label": f"Supplier {idx}",
            "name_internal": supplier.get("name_internal"),
            "primary_domain": supplier.get("primary_domain"),
            "year_founded": supplier.get("year_founded"),
            "headquarters_internal": supplier.get("headquarters_internal"),
            "headcount_total_internal": supplier.get("headcount_total_internal"),
            "industry": supplier.get("industry"),
            "product_line_status": supplier.get("product_line_status", "HUMAN_OR_SIMULATED"),
            "sources": supplier.get("sources", []),
            "confidence": supplier.get("confidence", 0.95),
        }
        clean_suppliers.append(record)

    return clean_suppliers


def to_supplier_display(supplier: Dict[str, Any]) -> Dict[str, Any]:
    """Projects supplier to screen display under Option C (labels & citations only)."""
    return {
        "display_label": supplier.get("display_label"),
        "sources": [
            {"field": s["field"], "endpoint": s["endpoint"]}
            for s in supplier.get("sources", [])
        ],
    }


def format_screen_display(suppliers: List[Dict[str, Any]], is_simulated: bool = False) -> str:
    """Format suppliers for screen display strictly adhering to Option C.

    Option C Rules (Section 8 & PR #10 contracts):
    - Screens show DISPLAY LABELS ("Supplier 1", "Supplier 2", ...) ONLY.
    - Citations only ("Source: Crustdata", endpoint, and field).
    - NEVER show company values (e.g. headcount numbers, city names, domain URLs).
    - NEVER show real company names on screen.
    - Real values and names remain strictly in internal logs (_internal).
    """
    lines = [
        "=================================================================",
        "          SUPPLIER DISCOVERY & VERIFICATION (SCREEN VIEW)         ",
        "  Display Rule: Option C (Display labels and citations only)     ",
    ]
    if is_simulated:
        lines.append("  Mode: SIMULATED fixture; no live Crustdata call                ")
    lines.extend([
        "=================================================================",
        "",
    ])

    source_suffix = " [SIMULATED fixture; no live Crustdata call]" if is_simulated else ""
    for supplier in suppliers:
        label = supplier.get("display_label", "Supplier")
        status = supplier.get("product_line_status", "HUMAN_OR_SIMULATED")
        if is_simulated and status == "CONFIRMED":
            status = "CONFIRMED (SIMULATED)"
        conf = supplier.get("confidence", 0.0)

        lines.append(f"[{label}] - Match Confidence: {conf:.0%}")
        for src in supplier.get("sources", []):
            field = src.get("field")
            endpoint = src.get("endpoint")
            extra = f" [{status}]" if field == "basic_info.description" else ""
            lines.append(f"  - {field}: Source: Crustdata ({endpoint}){extra}{source_suffix}")
        lines.append("")

    lines.append("--- Contract Screen Projection (JSON) ---")
    display_records = [to_supplier_display(s) for s in suppliers]
    lines.append(json.dumps(display_records, indent=2))
    lines.append("")
    lines.append("Note: Real company names and demographic metrics are logged internally in _internal fields.")
    return "\n".join(lines)


def format_internal_log(suppliers: List[Dict[str, Any]]) -> str:
    """Format complete internal log record with real names and metrics (not for screen)."""
    lines = [
        "--- INTERNAL AUDIT LOG (CONFIDENTIAL - DO NOT DISPLAY ON SCREEN) ---"
    ]
    for s in suppliers:
        lines.append(
            f"{s.get('display_label')}: Name={s.get('name_internal')}, "
            f"Domain={s.get('primary_domain')}, "
            f"HQ={s.get('headquarters_internal')}, "
            f"Headcount={s.get('headcount_total_internal')}, "
            f"Status={s.get('product_line_status')}, "
            f"Confidence={s.get('confidence')}"
        )
    return "\n".join(lines)
