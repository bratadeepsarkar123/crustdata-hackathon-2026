"""Tests for Deduplication (Step 4): domain and name matching, confidence scoring."""

import unittest

from src.discovery.dedupe import (
    dedupe_candidates,
    normalize_domain,
    normalize_company_name,
    compute_name_similarity,
)


class TestCrustdataDedupe(unittest.TestCase):

    def test_normalize_domain(self):
        self.assertEqual(normalize_domain("https://www.tempsens.com/"), "tempsens.com")
        self.assertEqual(normalize_domain("http://radix.co.in/products/sensors"), "radix.co.in")
        self.assertEqual(normalize_domain("WWW2.BAUMER.COM:8080"), "baumer.com")
        self.assertEqual(normalize_domain(""), "")

    def test_normalize_company_name(self):
        self.assertEqual(normalize_company_name("Tempsens Instruments Pvt. Ltd."), "tempsens instruments")
        self.assertEqual(normalize_company_name("Radix Electrosystems Private Limited"), "radix electrosystems")
        self.assertEqual(normalize_company_name("Baumer India Inc."), "baumer india")

    def test_compute_name_similarity(self):
        sim_exact = compute_name_similarity("Tempsens Instruments Pvt Ltd", "Tempsens Instruments")
        self.assertEqual(sim_exact, 1.0)

        sim_high = compute_name_similarity("Radix Electrosystems", "Radix Electrosystem Co")
        self.assertGreaterEqual(sim_high, 0.8)

        sim_diff = compute_name_similarity("Honeywell Automation", "Baumer Sensors")
        self.assertLess(sim_diff, 0.3)

    def test_dedupe_merges_duplicate_records(self):
        raw_candidates = [
            {
                "name_internal": "Tempsens Instruments",
                "primary_domain": "tempsens.com",
                "year_founded": 1976,
                "headquarters_internal": "Udaipur, India",
                "headcount_total_internal": 650,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "domain", "endpoint": "/company/search"}],
                "confidence": 0.90,
            },
            {
                # Duplicate with different domain formatting and legal suffix
                "name_internal": "Tempsens Instruments Pvt. Ltd.",
                "primary_domain": "https://www.tempsens.com/",
                "year_founded": 1976,
                "headquarters_internal": "Udaipur, Rajasthan, India",
                "headcount_total_internal": 650,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "headcount", "endpoint": "/company/enrich"}],
                "confidence": 0.85,
            },
            {
                # Distinct company
                "name_internal": "Radix Electrosystems",
                "primary_domain": "radix.co.in",
                "year_founded": 1980,
                "headquarters_internal": "Mumbai, India",
                "headcount_total_internal": 280,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "domain", "endpoint": "/company/search"}],
                "confidence": 0.92,
            },
        ]

        deduped = dedupe_candidates(raw_candidates)

        # 3 inputs merged into 2 unique suppliers
        self.assertEqual(len(deduped), 2)

        tempsens = next(s for s in deduped if s["primary_domain"] == "tempsens.com")
        self.assertIsNotNone(tempsens)
        # Check confidence updated
        self.assertGreaterEqual(tempsens["confidence"], 0.95)
        # Check sources combined
        self.assertEqual(len(tempsens["sources"]), 2)


if __name__ == "__main__":
    unittest.main()
