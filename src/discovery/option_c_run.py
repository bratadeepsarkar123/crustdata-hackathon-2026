#!/usr/bin/env python3
"""One-item supplier discovery and verification run enforcing Option C (labels & citations only).

Task 1 (Owner directives 2026-11-06):
Takes one item (neodymium speaker magnet, 3 mm, US buyer, sole supplier in China, very small MOQ),
runs search, identify, enrich, and dedupe through service.py, and prints only neutral "Supplier N"
labels with citations.

Live Crustdata calls only occur when explicitly requested via --live.
Default mode is 100% offline using simulated fixtures.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.crustdata.client import CrustdataClient, load_api_key_from_env
from src.crustdata.exceptions import CrustdataAPIError, CrustdataCreditsExhaustedError
from src.discovery.service import (
    format_internal_log,
    format_screen_display,
    run_discovery_pipeline,
    to_supplier_display,
)

logger = logging.getLogger("discovery.one_item")


def build_one_item_request(
    item: str = "neodymium speaker magnet",
    quantity: int = 1000,
    unit: str = "pcs",
    spec: str = "3 mm thick, low minimum order",
    buyer_location: str = "US",
    supplier_region: str = "China",
    moq: str = "very small",
) -> Dict[str, Any]:
    """Construct standard procurement request payload for the one-item flow."""
    return {
        "item": item,
        "quantity": quantity,
        "unit": unit,
        "spec": spec,
        "region": supplier_region,  # Target supplier country hard limit
        "buyer_location": buyer_location,
        "target_supplier_region": supplier_region,
        "moq": moq,
        "sole_source": True,
        "missing_fields": [],
    }


def to_shortlist_payload(
    suppliers: List[Dict[str, Any]],
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Convert discovered suppliers into the schema of samples/one-item/supplier-shortlist.json.

    Bridges Discovery output (Person 2) with the desk's one-item shortlist schema.
    """
    spec_thickness = 3
    if "3 mm" in request.get("spec", ""):
        spec_thickness = 3

    shortlist_suppliers = []
    for s in suppliers:
        claims = []
        sources_list = [f"{src['endpoint'].replace('POST /company/', '')}: {src['field']}" for src in s.get("sources", [])]
        citation_str = "company enrich: " + ", ".join([src["field"] for src in s.get("sources", []) if "enrich" in src.get("endpoint", "")])
        if not citation_str or citation_str == "company enrich: ":
            citation_str = "company identify: primary_domain"

        # Neutral summary statement
        claim_text = (
            f"Verified supplier profile, status {s.get('product_line_status')}, "
            f"confidence {s.get('confidence', 0.95):.0%}"
        )
        claims.append({
            "text": claim_text,
            "citation": citation_str,
        })

        shortlist_suppliers.append({
            "label": s.get("display_label", "Supplier"),
            "claims": claims,
        })

    return {
        "item": {
            "name": request.get("item", "neodymium speaker magnet"),
            "thickness_mm": spec_thickness,
            "quantity_pcs": request.get("quantity", 1000),
            "buyer_location": request.get("buyer_location", "US"),
        },
        "constraints": {
            "supplier_country": request.get("region", "China"),
            "sole_source": request.get("sole_source", True),
            "moq": request.get("moq", "very small"),
        },
        "suppliers": shortlist_suppliers,
        "recommended_label": suppliers[0].get("display_label") if suppliers else None,
    }


def run_one_item_discovery(
    item: str = "neodymium speaker magnet",
    quantity: int = 1000,
    unit: str = "pcs",
    spec: str = "3 mm thick, low minimum order",
    buyer_location: str = "US",
    supplier_region: str = "China",
    moq: str = "very small",
    live: bool = False,
    internal_log_file: Optional[str] = "discovery_internal_audit.log",
) -> List[Dict[str, Any]]:
    """Run end-to-end discovery and verification pipeline for a single item."""
    request = build_one_item_request(
        item=item,
        quantity=quantity,
        unit=unit,
        spec=spec,
        buyer_location=buyer_location,
        supplier_region=supplier_region,
        moq=moq,
    )

    client: Optional[CrustdataClient] = None
    use_fixtures = not live

    if live:
        api_key = load_api_key_from_env()
        if not api_key:
            raise CrustdataAPIError(
                "CRUSTDATA_API_KEY is not set in environment or .env. Cannot perform --live run."
            )
        client = CrustdataClient(api_key=api_key, allow_live=True)
        logger.info("Initialized live Crustdata client for one-item discovery")
    else:
        logger.info("Executing one-item discovery in offline SIMULATED fixture mode")

    suppliers = run_discovery_pipeline(
        request=request,
        client=client,
        use_fixtures=use_fixtures,
    )

    # Write internal audit log (confidential) if path specified
    if internal_log_file:
        try:
            log_content = format_internal_log(suppliers)
            with open(internal_log_file, "w", encoding="utf-8") as f:
                f.write(log_content + "\n")
            logger.info("Wrote confidential internal log to %s", internal_log_file)
        except OSError as exc:
            logger.warning("Could not write internal log file %s: %s", internal_log_file, exc)

    return suppliers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-item supplier discovery runner under Option C (labels & citations only)."
    )
    parser.add_argument(
        "--item",
        type=str,
        default="neodymium speaker magnet",
        help="Name of the required item (default: neodymium speaker magnet)",
    )
    parser.add_argument(
        "--quantity",
        type=int,
        default=1000,
        help="Required quantity (default: 1000)",
    )
    parser.add_argument(
        "--unit",
        type=str,
        default="pcs",
        help="Unit of measure (default: pcs)",
    )
    parser.add_argument(
        "--spec",
        type=str,
        default="3 mm thick, low minimum order",
        help="Item technical specifications (default: 3 mm thick, low minimum order)",
    )
    parser.add_argument(
        "--buyer-location",
        type=str,
        default="US",
        help="Buyer location (default: US)",
    )
    parser.add_argument(
        "--supplier-region",
        type=str,
        default="China",
        help="Target supplier country/region (default: China)",
    )
    parser.add_argument(
        "--moq",
        type=str,
        default="very small",
        help="Minimum order quantity constraint (default: very small)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Enable live Crustdata API calls (requires CRUSTDATA_API_KEY in environment)",
    )
    parser.add_argument(
        "--internal-log-file",
        type=str,
        default="discovery_internal_audit.log",
        help="Path for confidential internal log (default: discovery_internal_audit.log)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw Option C JSON screen projection only",
    )
    parser.add_argument(
        "--shortlist-json",
        action="store_true",
        default=False,
        help="Output JSON formatted according to samples/one-item/supplier-shortlist.json",
    )

    args = parser.parse_args()

    try:
        suppliers = run_one_item_discovery(
            item=args.item,
            quantity=args.quantity,
            unit=args.unit,
            spec=args.spec,
            buyer_location=args.buyer_location,
            supplier_region=args.supplier_region,
            moq=args.moq,
            live=args.live,
            internal_log_file=args.internal_log_file,
        )
    except CrustdataCreditsExhaustedError as exc:
        print(f"Discovery halted (credit guard): {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Discovery failed: {exc}", file=sys.stderr)
        return 1

    # Option C Output
    if args.shortlist_json:
        req = build_one_item_request(
            item=args.item,
            quantity=args.quantity,
            unit=args.unit,
            spec=args.spec,
            buyer_location=args.buyer_location,
            supplier_region=args.supplier_region,
            moq=args.moq,
        )
        shortlist = to_shortlist_payload(suppliers, req)
        output_str = json.dumps(shortlist, indent=2)
    elif args.json:
        display_only = [to_supplier_display(s) for s in suppliers]
        output_str = json.dumps(display_only, indent=2)
    else:
        output_str = format_screen_display(suppliers, is_simulated=(not args.live))

    # Security check: Ensure Option C compliance (zero company names in stdout)
    for s in suppliers:
        raw_name = s.get("name_internal")
        if raw_name and raw_name.lower() in output_str.lower():
            raise RuntimeError(
                f"Security violation: Company name '{raw_name}' leaked into screen output!"
            )
        raw_domain = s.get("primary_domain")
        if raw_domain and raw_domain.lower() in output_str.lower():
            raise RuntimeError(
                f"Security violation: Company domain '{raw_domain}' leaked into screen output!"
            )

    print(output_str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
