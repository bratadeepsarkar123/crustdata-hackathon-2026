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
        self.assertEqual(normalize_domain("https://www.alpha-thermal.example/"), "alpha-thermal.example")
        self.assertEqual(normalize_domain("http://bravo-electro.example/products/sensors"), "bravo-electro.example")
        self.assertEqual(normalize_domain("WWW2.CHARLIE-SENSORS.EXAMPLE:8080"), "charlie-sensors.example")
        self.assertEqual(normalize_domain(""), "")

    def test_normalize_company_name(self):
        self.assertEqual(normalize_company_name("Alpha Thermal Pvt. Ltd."), "alpha thermal")
        self.assertEqual(normalize_company_name("Bravo Electro Private Limited"), "bravo electro")
        self.assertEqual(normalize_company_name("Charlie Sensors Inc."), "charlie sensors")

    def test_compute_name_similarity(self):
        sim_exact = compute_name_similarity("Alpha Thermal Pvt Ltd", "Alpha Thermal")
        self.assertEqual(sim_exact, 1.0)

        sim_high = compute_name_similarity("Bravo Electro", "Bravo Electro Co")
        self.assertGreaterEqual(sim_high, 0.8)

        sim_diff = compute_name_similarity("Foxtrot Automation", "Charlie Sensors")
        self.assertLess(sim_diff, 0.3)

    def test_dedupe_merges_duplicate_records(self):
        raw_candidates = [
            {
                "name_internal": "Alpha Thermal",
                "primary_domain": "alpha-thermal.example",
                "year_founded": 1976,
                "headquarters_internal": "City A, India",
                "headcount_total_internal": 650,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "domain", "endpoint": "/company/search"}],
                "confidence": 0.90,
            },
            {
                # Duplicate with different domain formatting and legal suffix
                "name_internal": "Alpha Thermal Pvt. Ltd.",
                "primary_domain": "https://www.alpha-thermal.example/",
                "year_founded": 1976,
                "headquarters_internal": "City A, Region A, India",
                "headcount_total_internal": 650,
                "product_line_status": "CONFIRMED",
                "sources": [{"field": "headcount", "endpoint": "/company/enrich"}],
                "confidence": 0.85,
            },
            {
                # Distinct company
                "name_internal": "Bravo Electro",
                "primary_domain": "bravo-electro.example",
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

        alpha = next(s for s in deduped if s["primary_domain"] == "alpha-thermal.example")
        self.assertIsNotNone(alpha)
        # Check confidence updated
        self.assertGreaterEqual(alpha["confidence"], 0.95)
        # Check sources combined
        self.assertEqual(len(alpha["sources"]), 2)


if __name__ == "__main__":
    unittest.main()
