"""Tests for Crustdata fixture execution across Steps 2, 3, 4."""

import unittest

from src.discovery.service import run_discovery_pipeline


class TestCrustdataFixtures(unittest.TestCase):

    def test_fixture_run_end_to_end(self):
        request = {
            "item": "industrial temperature sensors",
            "quantity": 500,
            "budget": 25000,
            "currency": "USD",
            "deadline_days": 14,
            "region": "India",
            "missing_fields": [],
        }

        suppliers = run_discovery_pipeline(request, use_fixtures=True)

        # 6 raw candidates deduplicated to 5 unique suppliers
        self.assertEqual(len(suppliers), 5)

        required_keys = [
            "display_label",
            "name_internal",
            "primary_domain",
            "year_founded",
            "headquarters_internal",
            "headcount_total_internal",
            "industry",
            "product_line_status",
            "sources",
            "confidence",
        ]

        confirmed_count = 0
        human_simulated_count = 0

        for idx, s in enumerate(suppliers, start=1):
            for k in required_keys:
                self.assertIn(k, s, f"Supplier missing required contract key '{k}'")

            self.assertEqual(s["display_label"], f"Supplier {idx}")
            self.assertGreater(s["confidence"], 0.0)
            self.assertGreater(len(s["sources"]), 0)

            if s["product_line_status"] == "CONFIRMED":
                confirmed_count += 1
            elif s["product_line_status"] == "HUMAN_OR_SIMULATED":
                human_simulated_count += 1

        self.assertGreater(confirmed_count, 0)
        self.assertGreater(human_simulated_count, 0)


if __name__ == "__main__":
    unittest.main()
