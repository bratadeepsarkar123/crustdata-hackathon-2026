"""Demo citation script for ContextCon 04 (Option C Display Rule).

Runs discovery and verification on fixtures and outputs screen-ready facts
with citations (Source: Crustdata, endpoint, field) and neutral labels only.
"""

from __future__ import annotations

import json
import sys

from src.discovery.service import run_discovery_pipeline, format_screen_display, format_internal_log


def run_demo(category: str = "industrial temperature sensors", region: str = "India") -> int:
    request = {
        "item": category,
        "quantity": 500,
        "budget": 25000,
        "currency": "USD",
        "deadline_days": 14,
        "region": region,
        "missing_fields": [],
    }

    print("=" * 70)
    print("CONTEXTCON 04 - DEMO CITATION RUNNER (PERSON 2: DISCOVERY & CRUSTDATA)")
    print(f"Request: {request['quantity']} {request['item']} in {request['region']} (Budget: ${request['budget']})")
    print("=" * 70)
    print()

    # Run discovery on fixtures (offline, zero credit spend)
    suppliers = run_discovery_pipeline(request=request, use_fixtures=True)

    # 1. Option C Screen Display (what the judges and screens see)
    screen_output = format_screen_display(suppliers)
    print(screen_output)
    print()

    # 2. Verify Option C Compliance
    real_names = [s.get("name_internal") for s in suppliers if s.get("name_internal")]
    forbidden_in_screen = [name for name in real_names if name in screen_output]
    if forbidden_in_screen:
        print(f"ERROR: Real company names leaked to screen: {forbidden_in_screen}", file=sys.stderr)
        return 1

    print("Option C Verification: PASSED. All screens show display labels & citations only.")
    print("All internal names and metrics are strictly preserved in internal logs.")
    print()

    # 3. Print internal log header snippet
    print(format_internal_log(suppliers))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(run_demo())
