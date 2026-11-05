"""Deduplication of candidate suppliers by domain and company name (Step 4)."""

from __future__ import annotations

import difflib
import re
from typing import Any, Dict, List
import urllib.parse


def normalize_domain(domain: str | None) -> str:
    """Normalize domain by stripping protocol, www, trailing slashes, and paths."""
    if not domain:
        return ""
    d = domain.strip().lower()
    if "://" in d:
        try:
            parsed = urllib.parse.urlparse(d)
            d = parsed.netloc or parsed.path
        except Exception:
            pass
    # Strip common prefixes/suffixes
    d = re.sub(r"^www\d*\.", "", d)
    d = d.split("/")[0].split(":")[0].strip()
    return d


def normalize_company_name(name: str | None) -> str:
    """Normalize company name by stripping legal entities, punctuation and spacing."""
    if not name:
        return ""
    s = name.lower()
    # Remove punctuation
    s = re.sub(r"[^\w\s]", " ", s)
    # Remove corporate designators
    suffixes = [
        r"\bpvt\s+ltd\b",
        r"\bprivate\s+limited\b",
        r"\bltd\b",
        r"\blimited\b",
        r"\binc\b",
        r"\bincorporated\b",
        r"\bcorp\b",
        r"\bcorporation\b",
        r"\bllc\b",
        r"\bgmbh\b",
        r"\bco\b",
        r"\bcompany\b",
    ]
    for pattern in suffixes:
        s = re.sub(pattern, " ", s)
    # Collapse whitespace
    tokens = [t for t in s.split() if len(t) > 1]
    return " ".join(tokens)


def compute_name_similarity(name1: str, name2: str) -> float:
    """Compute similarity between two normalized company names using token overlap and sequence matching."""
    norm1 = normalize_company_name(name1)
    norm2 = normalize_company_name(name2)
    if not norm1 or not norm2:
        return 0.0
    if norm1 == norm2:
        return 1.0

    # 1. Sequence similarity (handles plurals, typos, stemming)
    seq_ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()

    # 2. Token-based Jaccard similarity
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    token_sim = (len(intersection) / len(union)) if union else 0.0

    return max(seq_ratio, token_sim)


def dedupe_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate candidates within the search window.

    Matches by:
    1. Exact normalized primary domain match (confidence ~0.95-0.98)
    2. High normalized company name similarity (confidence ~0.85-0.92)

    Merges duplicates into a single record preserving citations and best values.
    """
    deduped: List[Dict[str, Any]] = []

    for cand in candidates:
        cand_domain = normalize_domain(cand.get("primary_domain") or cand.get("domain"))
        cand_name = cand.get("name_internal") or cand.get("name") or ""

        matched_index = -1
        match_confidence = 1.0

        for idx, existing in enumerate(deduped):
            ex_domain = normalize_domain(existing.get("primary_domain") or existing.get("domain"))
            ex_name = existing.get("name_internal") or existing.get("name") or ""

            # Check 1: Domain match
            if cand_domain and ex_domain and cand_domain == ex_domain:
                matched_index = idx
                match_confidence = 0.98
                break

            # Check 2: High name similarity
            sim = compute_name_similarity(cand_name, ex_name)
            if sim >= 0.8:
                matched_index = idx
                match_confidence = round(0.85 + (sim * 0.1), 2)
                break

        if matched_index >= 0:
            # Merge candidate into existing record
            existing = deduped[matched_index]
            # Update confidence
            existing["confidence"] = max(existing.get("confidence", 0.0), match_confidence)

            # Combine citations/sources without duplicates
            existing_sources = existing.setdefault("sources", [])
            new_sources = cand.get("sources", [])
            for s in new_sources:
                if s not in existing_sources:
                    existing_sources.append(s)

            # Preserve non-empty fields
            for k in ["year_founded", "headquarters_internal", "headcount_total_internal", "industry"]:
                if not existing.get(k) and cand.get(k):
                    existing[k] = cand[k]

            # Preserve confirmed product line status if either is confirmed
            if cand.get("product_line_status") == "CONFIRMED":
                existing["product_line_status"] = "CONFIRMED"
        else:
            # New unique candidate
            new_record = dict(cand)
            if "confidence" not in new_record:
                new_record["confidence"] = 0.95
            if cand_domain:
                new_record["primary_domain"] = cand_domain
            deduped.append(new_record)

    return deduped
