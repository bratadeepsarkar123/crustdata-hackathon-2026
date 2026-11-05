"""Tests for Crustdata Discovery (Step 2): ranked search, location hard limits, autocomplete."""

import unittest
from unittest.mock import MagicMock

from src.crustdata.client import CrustdataClient
from src.discovery.candidate_search import search_candidate_suppliers, resolve_industry_filter


class TestCrustdataDiscovery(unittest.TestCase):

    def test_discovery_with_fixtures(self):
        request = {
            "item": "temperature sensors",
            "quantity": 500,
            "region": "India",
        }
        candidates = search_candidate_suppliers(request=request, use_fixtures=True)
        self.assertGreaterEqual(len(candidates), 5)
        for cand in candidates:
            self.assertIn("name_internal", cand)
            self.assertIn("primary_domain", cand)
            self.assertTrue(cand["primary_domain"])
            self.assertEqual(cand["product_line_status"], "HUMAN_OR_SIMULATED")
            # Verify citations recorded
            endpoints = [s["endpoint"] for s in cand["sources"]]
            self.assertIn("/company/search", endpoints)

    def test_discovery_location_hard_limit(self):
        request = {
            "item": "temperature sensors",
            "region": "India",
        }
        candidates = search_candidate_suppliers(request=request, use_fixtures=True)
        for cand in candidates:
            self.assertIn("India", cand["headquarters_internal"])

    def test_ranked_search_live_call_structure(self):
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.company_search.return_value = {
            "results": [
                {
                    "name": "Live Sensor Co",
                    "domain": "livesensors.com",
                    "year_founded": 2005,
                    "location": "Bengaluru, India",
                    "relevance_score": 0.95,
                }
            ]
        }

        request = {"item": "pressure sensors", "region": "India"}
        res = search_candidate_suppliers(request=request, client=mock_client, use_fixtures=False)

        # Verify client.company_search was called with ranked search
        mock_client.company_search.assert_called_once_with(
            query="pressure sensors",
            filters=[{
                "filter_type": "CURRENT_LOCATION",
                "type": "country",
                "value": ["India"],
            }],
            limit=100,
            ranked=True,
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name_internal"], "Live Sensor Co")

    def test_autocomplete_before_industry_filter(self):
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.company_autocomplete.return_value = {
            "suggestions": [{"value": "Sensors & Measuring Instruments"}]
        }

        resolved = resolve_industry_filter(mock_client, "sensors", use_fixtures=False)
        mock_client.company_autocomplete.assert_called_once_with(query="sensors")
        self.assertEqual(resolved, "Sensors & Measuring Instruments")

    def test_filters_only_fallback_when_ranked_empty(self):
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        # First call (ranked) returns empty list; second call (filters-only) returns result
        mock_client.company_search.side_effect = [
            {"results": []},
            {"results": [{"name": "Fallback Co", "domain": "fallback.com", "relevance_score": 0.70}]},
        ]

        request = {"item": "niche sensors", "region": "India"}
        candidates = search_candidate_suppliers(request=request, client=mock_client, use_fixtures=False)

        self.assertEqual(mock_client.company_search.call_count, 2)
        # Verify fallback call used ranked=False
        second_call_kwargs = mock_client.company_search.call_args_list[1][1]
        self.assertFalse(second_call_kwargs["ranked"])
        self.assertIsNone(second_call_kwargs["query"])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["name_internal"], "Fallback Co")


if __name__ == "__main__":
    unittest.main()
