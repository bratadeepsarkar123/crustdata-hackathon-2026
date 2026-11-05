"""Candidate discovery using Crustdata ranked search, location limits and autocomplete (Step 2)."""

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
) -> str:
    """Resolve industry to Crustdata's closed set via company_autocomplete before filtering."""
    if use_fixtures or not client or not client.allow_live:
        for suggestion in FIXTURE_INDUSTRY_AUTOCOMPLETE["suggestions"]:
            if industry_query.lower() in suggestion.lower():
                return suggestion
        return FIXTURE_INDUSTRY_AUTOCOMPLETE["suggestions"][0]

    try:
        res = client.company_autocomplete(query=industry_query)
        suggestions = res.get("suggestions") or res.get("results") or []
        if suggestions:
            if isinstance(suggestions[0], dict):
                return suggestions[0].get("value") or suggestions[0].get("name") or industry_query
            return str(suggestions[0])
    except (CrustdataCreditsExhaustedError, CrustdataPlanGatedError, CrustdataRateLimitError):
        raise
    except Exception as exc:
        logger.warning("Industry autocomplete resolution failed: %s; falling back to original", exc)

    return industry_query


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
                credit_guard.estimate_and_check(0.03)
            res = client.company_search(
                query=item_query,
                filters=filters if filters else None,
                limit=100,
                ranked=True,
            )
            raw_candidates = res.get("results") or res.get("companies") or []
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
                    credit_guard.estimate_and_check(0.03)
                res = client.company_search(
                    query=None,
                    filters=filters if filters else None,
                    limit=100,
                    ranked=False,
                )
                raw_candidates = res.get("results") or res.get("companies") or []
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
        cand = {
            "name_internal": item.get("name", "Unknown Supplier"),
            "primary_domain": item.get("domain", ""),
            "year_founded": item.get("year_founded"),
            "industry": item.get("industry", resolved_industry or "Industrial Equipment"),
            "headquarters_internal": item.get("location", ""),
            "headcount_total_internal": None,  # Will be fetched on enrich
            "product_line_status": "HUMAN_OR_SIMULATED",  # Verified in Step 3
            "sources": [
                {"field": "primary_domain", "endpoint": "POST /company/identify"},
            ],
            "confidence": round(float(item.get("relevance_score", 0.90)), 2),
        }
        candidates.append(cand)

    return candidates
