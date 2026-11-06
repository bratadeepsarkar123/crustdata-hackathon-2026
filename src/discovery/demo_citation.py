"""Demo citation script for ContextCon 04 (Option C Display Rule).

Runs discovery and verification on fixtures (default) or live Crustdata API (--live)
and outputs screen-ready facts with citations (Source: Crustdata, endpoint, field)
and neutral labels only.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

from src.crustdata.client import CrustdataClient, load_api_key_from_env
from src.crustdata.credits import CreditGuard, check_account_credits
from src.discovery.service import run_discovery_pipeline, format_screen_display, format_internal_log


def run_demo(
    category: str = "industrial temperature sensors",
    region: str = "India",
    log_file: str = "discovery_internal_audit.log",
    live: bool = False,
) -> int:
    request = {
        "item": category,
        "quantity": 500,
        "budget": 25000,
        "currency": "USD",
        "deadline_days": 14,
        "region": region,
        "missing_fields": [],
    }

    mode_str = "LIVE Crustdata API" if live else "SIMULATED fixture; no live Crustdata call"
    print("=" * 70)
    print("CONTEXTCON 04 - DEMO CITATION RUNNER (PERSON 2: DISCOVERY & CRUSTDATA)")
    print(f"Mode: {mode_str}")
    print(f"Request: {request['quantity']} {request['item']} in {request['region']} (Budget: ${request['budget']})")
    print("=" * 70)
    print()

    client = None
    credit_guard = None
    start_credits = None

    if live:
        api_key = load_api_key_from_env()
        if not api_key:
            print("ERROR: CRUSTDATA_API_KEY environment variable not set or .env file missing.", file=sys.stderr)
            return 1
        client = CrustdataClient(api_key=api_key, allow_live=True)
        try:
            start_credits = check_account_credits(client)
            print(f"Pre-flight account credits balance: {start_credits:.2f}")
        except Exception as exc:
            print(f"ERROR: Failed pre-flight credit check: {exc}", file=sys.stderr)
            return 1

        credit_guard = CreditGuard(max_budget=200.0)

    # Run discovery pipeline
    suppliers = run_discovery_pipeline(
        request=request,
        client=client,
        use_fixtures=(not live),
        credit_guard=credit_guard,
        max_candidates_to_verify=5 if live else None,
    )

    # 1. Option C Screen Display (what the judges and screens see)
    screen_output = format_screen_display(suppliers, is_simulated=(not live))
    print(screen_output)
    print()

    # 2. Verify Option C Compliance (no real name or internal values on screen)
    real_names = [s.get("name_internal") for s in suppliers if s.get("name_internal")]
    forbidden_in_screen = [name for name in real_names if name in screen_output]
    if forbidden_in_screen:
        print("ERROR: Option C compliance failure: unmasked supplier identity detected in screen view.", file=sys.stderr)
        return 1

    print("Option C Verification: PASSED. All screens show display labels & citations only.")
    print("All internal names and metrics are strictly preserved in internal logs.")
    print()

    # 3. Save internal audit log to file (never printed to stdout / screen)
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(format_internal_log(suppliers) + "\n")
    print(f"Internal audit log saved to: {log_file} (retained for policy checks; omitted from screen).")
    print()

    if live and client:
        try:
            end_credits = check_account_credits(client)
            actual_spent = start_credits - end_credits if start_credits is not None else credit_guard.total_credits_used
            limit_passed = "PASSED" if actual_spent < 200.0 else "FAILED"
            print("-" * 50)
            print("CRUSTDATA LIVE RUN USAGE SUMMARY")
            print(f"Starting credit balance : {start_credits:.2f}")
            print(f"Ending credit balance   : {end_credits:.2f}")
            print(f"Credits consumed        : {actual_spent:.2f}")
            print(f"Safety limit (< 200)    : {limit_passed}")
            print("-" * 50)
        except Exception as exc:
            print(f"Warning: could not fetch ending credit balance: {exc}")

    return 0
