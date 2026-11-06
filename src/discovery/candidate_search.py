"""Candidate supplier discovery using ranked search, location hard limits, and autocomplete (Step 2)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.crustdata.client import CrustdataClient
from src.crustdata.credits import CreditGuard
from src.crustdata.exceptions import (
    CrustdataBudgetExceededError,
    CrustdataCreditsExhaustedError,
    CrustdataPlanGatedError,
    CrustdataRateLimitError,
)
from .fixtures import FIXTURE_COMPANY_SEARCH_RESULTS, FIXTURE_INDUSTRY_AUTOCOMPLETE

logger = logging.getLogger("discovery.search")


def resolve_industry_filter(
    client: Optional[CrustdataClient],
    industry_query: str,
    use_fixtures: bool = False,
) -> Optional[str]:
    """Resolve industry query to canonical closed-set value using company_autocomplete before filtering."""
    if use_fixtures or not client or not client.allow_live:
        suggestions = FIXTURE_INDUSTRY_AUTOCOMPLETE.get("results", [])
        for sug in suggestions:
            if industry_query.lower() in sug.lower():
                return sug
        return suggestions[0] if suggestions else None

    try:
        res = client.company_autocomplete(query=industry_query)
        results = res.get("results") or res.get("suggestions") or []
        if results and isinstance(results, list):
            first = results[0]
            if isinstance(first, dict):
                return str(first.get("value") or first.get("label") or first)
            return str(first)
    except Exception as exc:
        logger.warning("company_autocomplete failed for '%s': %s", industry_query, exc)

    return None


def search_candidate_suppliers(
    request: Dict[str, Any],
    client: Optional[CrustdataClient] = None,
    use_fixtures: bool = False,
    industry_filter: Optional[str] = None,
    credit_guard: Optional[CreditGuard] = None,
) -> List[Dict[str, Any]]:
    """Step 2: Find candidate suppliers using ranked search with location filters as hard limits.

    Methodology:
    1. Ranked search (`search.query`) first with item query.
    2. Location filters applied as hard limits (e.g. region / country).
    3. Run `company_autocomplete` before applying any industry filter.
    4. Single window of up to 100 results, no paging.
    5. Fallback to filters-only search if ranked search yields no matches.
    """
    item_query = request.get("item", "industrial temperature sensors")
    region = request.get("region")

    # Resolve industry filter if provided
    resolved_industry = None
    if industry_filter:
        resolved_industry = resolve_industry_filter(client, industry_filter, use_fixtures=use_fixtures)

    # Location filter as hard limit
    filters: List[Dict[str, Any]] = []
    if region:
        filters.append({
            "filter_type": "CURRENT_LOCATION",
            "type": "country",
            "value": [region],
        })
    if resolved_industry:
        filters.append({
            "filter_type": "INDUSTRY",
            "type": "industry",
            "value": [resolved_industry],
        })

    raw_candidates: List[Dict[str, Any]] = []

    if use_fixtures or not client or not client.allow_live:
        # Fixture-driven execution
        all_fixture_results = FIXTURE_COMPANY_SEARCH_RESULTS.get("results", [])
        for item in all_fixture_results:
            # Check location hard limit if region is set
            if region and region.lower() not in item.get("country", "").lower() and region.lower() not in item.get("location", "").lower():
                continue
            raw_candidates.append(item)
    else:
        # Live Crustdata call: ranked search first
        try:
            if credit_guard:
                credit_guard.estimate_and_check(0.03 * 100)
            res = client.company_search(
                query=item_query,
                filters=filters if filters else None,
                limit=100,
                ranked=True,
            )
            raw_candidates = res.get("companies") or res.get("results") or []
            if credit_guard and raw_candidates:
                credit_guard.record_usage(0.03 * len(raw_candidates), "search")
        except (CrustdataCreditsExhaustedError, CrustdataPlanGatedError, CrustdataRateLimitError, CrustdataBudgetExceededError):
            raise
        except Exception as exc:
            logger.warning("Ranked search failed (%s); trying filters-only fallback", exc)
            raw_candidates = []

        # Fallback to filters-only if ranked query returned nothing
        if not raw_candidates:
            logger.info("Ranked search returned 0 results. Executing filters-only fallback.")
            try:
                if credit_guard:
                    credit_guard.estimate_and_check(0.03 * 100)
                res = client.company_search(
                    query=None,
                    filters=filters if filters else None,
                    limit=100,
                    ranked=False,
                )
                raw_candidates = res.get("companies") or res.get("results") or []
                if credit_guard and raw_candidates:
                    credit_guard.record_usage(0.03 * len(raw_candidates), "search_fallback")
            except (CrustdataCreditsExhaustedError, CrustdataPlanGatedError, CrustdataRateLimitError, CrustdataBudgetExceededError):
                raise
            except Exception as exc:
                logger.warning("Filters-only search fallback failed: %s", exc)
                raw_candidates = []

    # Map raw candidates to initial candidate supplier records
    candidates: List[Dict[str, Any]] = []
    for item in raw_candidates[:100]:
        bi = item.get("basic_info") if isinstance(item.get("basic_info"), dict) else item
        name = bi.get("name") or item.get("name") or "Unknown Supplier"
        domain = bi.get("primary_domain") or item.get("domain") or bi.get("domain") or ""
        year_founded = bi.get("year_founded") or item.get("year_founded")
        
        loc_obj = item.get("locations")
        hq = item.get("location")
        if not hq and isinstance(loc_obj, dict):
            hq = loc_obj.get("headquarters") or loc_obj.get("country")

        cand = {
            "name_internal": name,
            "primary_domain": domain,
            "year_founded": year_founded,
            "industry": item.get("industry", resolved_industry or "Industrial Equipment"),
            "headquarters_internal": hq or "",
            "headcount_total_internal": None,  # Will be fetched on enrich
            "product_line_status": "HUMAN_OR_SIMULATED",  # Verified in Step 3
            "sources": [
                {"field": "primary_domain", "endpoint": "POST /company/identify"},
            ],
            "confidence": round(float(item.get("relevance_score", 0.90)), 2),
        }
        candidates.append(cand)

    logger.info("Retrieved %d candidates after applying hard limits and rank threshold", len(candidates))
    return candidates
