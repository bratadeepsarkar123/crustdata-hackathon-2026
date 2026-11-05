"""Supplier verification via Crustdata identify (free) and enrich (2 credits) (Step 3)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.crustdata.client import CrustdataClient
from src.crustdata.exceptions import (
    CrustdataCreditsExhaustedError,
    CrustdataPlanGatedError,
    CrustdataRateLimitError,
)
from .fixtures import FIXTURE_COMPANY_ENRICH_MAP, FIXTURE_COMPANY_IDENTIFY_MAP
from .dedupe import normalize_domain

logger = logging.getLogger("discovery.verify")


def verify_supplier(
    candidate: Dict[str, Any],
    client: Optional[CrustdataClient] = None,
    use_fixtures: bool = False,
) -> Dict[str, Any]:
    """Step 3: Verify company candidate.

    Protocol per Section 4 & 7:
    1. Call POST /company/identify (Free).
       NEVER request headcount or locations on identify (plan-gated 403).
    2. If identified, call POST /company/enrich (2 credits per match)
       requesting: ["headcount", "locations", "basic_info"].
    3. Product-line check:
       Examine `basic_info.description`.
       - If non-empty -> product_line_status = "CONFIRMED"
       - If empty -> product_line_status = "HUMAN_OR_SIMULATED"
    """
    verified = dict(candidate)
    domain = normalize_domain(candidate.get("primary_domain"))
    name = candidate.get("name_internal", "")

    company_id: Optional[int] = None
    enrich_data: Optional[Dict[str, Any]] = None

    if use_fixtures or not client or not client.allow_live:
        # Fixture-driven verification
        id_info = FIXTURE_COMPANY_IDENTIFY_MAP.get(domain)
        if not id_info:
            # Try fuzzy matching domain in map
            for d_key, info in FIXTURE_COMPANY_IDENTIFY_MAP.items():
                if d_key in domain or domain in d_key:
                    id_info = info
                    break

        if id_info and id_info.get("verified", False):
            company_id = id_info.get("crustdata_company_id")
            enrich_data = FIXTURE_COMPANY_ENRICH_MAP.get(company_id)
    else:
        # 1. POST /company/identify (free)
        # Note: Do NOT request headcount or locations on identify
        try:
            ident_res = client.company_identify(
                names=[name] if name else None,
                domains=[domain] if domain else None,
            )
            # Crustdata identify typically returns company info with crustdata_company_id
            if isinstance(ident_res, dict):
                company_id = ident_res.get("crustdata_company_id")
                if not company_id and "results" in ident_res and ident_res["results"]:
                    company_id = ident_res["results"][0].get("crustdata_company_id")
        except (CrustdataCreditsExhaustedError, CrustdataPlanGatedError, CrustdataRateLimitError):
            # Critical API errors must stop the entire run immediately
            raise
        except Exception as exc:
            logger.warning("Identify failed for %s (%s): %s", name, domain, exc)
            company_id = None

        # 2. POST /company/enrich (2 credits per match) if identified
        if company_id:
            try:
                enrich_data = client.company_enrich(
                    company_id=company_id,
                    fields=["headcount", "locations", "basic_info"],
                )
            except (CrustdataCreditsExhaustedError, CrustdataPlanGatedError, CrustdataRateLimitError):
                # Critical API errors must stop the entire run immediately
                raise
            except Exception as exc:
                logger.warning("Enrich failed for company_id %s: %s", company_id, exc)
                enrich_data = None

    # Process verification outcome
    sources: List[Dict[str, str]] = list(verified.get("sources", []))

    if enrich_data:
        # Headcount
        headcount_obj = enrich_data.get("headcount", {})
        total_hc = headcount_obj.get("total") if isinstance(headcount_obj, dict) else headcount_obj
        verified["headcount_total_internal"] = total_hc
        if {"field": "headcount", "endpoint": "/company/enrich"} not in sources:
            sources.append({"field": "headcount", "endpoint": "/company/enrich"})

        # Locations
        loc_obj = enrich_data.get("locations", {})
        hq = loc_obj.get("headquarters") if isinstance(loc_obj, dict) else loc_obj
        if hq:
            verified["headquarters_internal"] = hq
        if {"field": "locations", "endpoint": "/company/enrich"} not in sources:
            sources.append({"field": "locations", "endpoint": "/company/enrich"})

        # Product-line check via basic_info.description
        basic_info = enrich_data.get("basic_info", {})
        description = basic_info.get("description", "") if isinstance(basic_info, dict) else ""

        if description and len(description.strip()) > 0:
            verified["product_line_status"] = "CONFIRMED"
        else:
            verified["product_line_status"] = "HUMAN_OR_SIMULATED"

        if {"field": "basic_info.description", "endpoint": "/company/enrich"} not in sources:
            sources.append({"field": "basic_info.description", "endpoint": "/company/enrich"})

        verified["confidence"] = max(verified.get("confidence", 0.0), 0.95)
    else:
        # Company could not be verified via Crustdata
        verified["product_line_status"] = "HUMAN_OR_SIMULATED"
        verified["confidence"] = min(verified.get("confidence", 0.5), 0.5)

    verified["sources"] = sources
    return verified


def verify_all_candidates(
    candidates: List[Dict[str, Any]],
    client: Optional[CrustdataClient] = None,
    use_fixtures: bool = False,
) -> List[Dict[str, Any]]:
    """Verify each candidate in the candidate list."""
    return [verify_supplier(cand, client=client, use_fixtures=use_fixtures) for cand in candidates]
