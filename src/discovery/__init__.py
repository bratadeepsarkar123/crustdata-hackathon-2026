"""Supplier discovery, verification and deduplication package."""

from .candidate_search import search_candidate_suppliers, resolve_industry_filter
from .verify import verify_supplier, verify_all_candidates
from .dedupe import dedupe_candidates, normalize_domain, normalize_company_name
from .service import run_discovery_pipeline, format_screen_display, format_internal_log
from .demo_citation import run_demo

__all__ = [
    "search_candidate_suppliers",
    "resolve_industry_filter",
    "verify_supplier",
    "verify_all_candidates",
    "dedupe_candidates",
    "normalize_domain",
    "normalize_company_name",
    "run_discovery_pipeline",
    "format_screen_display",
    "format_internal_log",
    "run_demo",
]
