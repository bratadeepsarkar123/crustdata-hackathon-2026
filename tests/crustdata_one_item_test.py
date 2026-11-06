"""Tests for one-item supplier discovery and Option C verification (Task 1 & Task 2)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from src.crustdata.client import CrustdataClient
from src.crustdata.exceptions import CrustdataAPIError, CrustdataCreditsExhaustedError
from src.discovery.option_c_run import (
    build_one_item_request,
    run_one_item_discovery,
    to_shortlist_payload,
)
from src.discovery.service import format_screen_display


class TestOneItemDiscovery(unittest.TestCase):

    def setUp(self):
        self.item = "neodymium speaker magnet"
        self.quantity = 1000
        self.unit = "pcs"
        self.spec = "3 mm thick, low minimum order"
        self.buyer_location = "US"
        self.supplier_region = "China"
        self.moq = "very small"

    def test_build_one_item_request_shape(self):
        req = build_one_item_request(
            item=self.item,
            quantity=self.quantity,
            unit=self.unit,
            spec=self.spec,
            buyer_location=self.buyer_location,
            supplier_region=self.supplier_region,
            moq=self.moq,
        )
        self.assertEqual(req["item"], "neodymium speaker magnet")
        self.assertEqual(req["quantity"], 1000)
        self.assertEqual(req["unit"], "pcs")
        self.assertEqual(req["spec"], "3 mm thick, low minimum order")
        self.assertEqual(req["region"], "China")
        self.assertEqual(req["buyer_location"], "US")
        self.assertEqual(req["moq"], "very small")
        self.assertTrue(req["sole_source"])

    def test_one_item_discovery_offline_fixtures(self):
        """Offline fixture execution returns 5 verified neodymium magnet suppliers in China."""
        suppliers = run_one_item_discovery(
            item=self.item,
            quantity=self.quantity,
            unit=self.unit,
            spec=self.spec,
            buyer_location=self.buyer_location,
            supplier_region=self.supplier_region,
            moq=self.moq,
            live=False,
        )
        self.assertEqual(len(suppliers), 5)

        for idx, s in enumerate(suppliers, start=1):
            self.assertEqual(s["display_label"], f"Supplier {idx}")
            self.assertEqual(s["product_line_status"], "CONFIRMED")
            self.assertGreater(s["confidence"], 0.8)
            # Verify citations contain identify and enrich endpoints
            endpoints = {src["endpoint"] for src in s.get("sources", [])}
            self.assertIn("POST /company/identify", endpoints)
            self.assertIn("POST /company/enrich", endpoints)

    def test_no_company_name_in_screen_output(self):
        """Strict Option C check: no internal company names or domains leak to the screen."""
        suppliers = run_one_item_discovery(
            item=self.item,
            quantity=self.quantity,
            unit=self.unit,
            spec=self.spec,
            buyer_location=self.buyer_location,
            supplier_region=self.supplier_region,
            moq=self.moq,
            live=False,
        )
        screen_output = format_screen_display(suppliers, is_simulated=True)

        for s in suppliers:
            name_internal = s.get("name_internal")
            domain_internal = s.get("primary_domain")
            hq_internal = s.get("headquarters_internal")
            hc_internal = str(s.get("headcount_total_internal"))

            self.assertTrue(name_internal, "Expected name_internal to exist in internal record")
            self.assertNotIn(
                name_internal.lower(),
                screen_output.lower(),
                f"Security violation: Company name '{name_internal}' leaked to screen display!",
            )
            self.assertNotIn(
                domain_internal.lower(),
                screen_output.lower(),
                f"Security violation: Domain '{domain_internal}' leaked to screen display!",
            )
            # Check headquarters and headcount are not leaked
            if hq_internal:
                self.assertNotIn(
                    hq_internal.lower(),
                    screen_output.lower(),
                    f"Security violation: Headquarters '{hq_internal}' leaked to screen display!",
                )
            if hc_internal and hc_internal != "None":
                self.assertNotIn(
                    hc_internal,
                    screen_output,
                    f"Security violation: Headcount '{hc_internal}' leaked to screen display!",
                )

            # No raw domain URLs in screen output
            self.assertNotIn(".example", screen_output.lower())
            self.assertNotIn("http://", screen_output.lower())
            self.assertNotIn("https://", screen_output.lower())

    def test_cli_option_c_run_execution(self):
        """Run CLI option_c_run.py script directly and verify exit code and stdout."""
        cmd = [sys.executable, "src/discovery/option_c_run.py"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, f"CLI exited with error: {proc.stderr}")

        stdout = proc.stdout
        self.assertIn("[Supplier 1]", stdout)
        self.assertIn("Option C", stdout)
        self.assertIn("SIMULATED fixture", stdout)
        self.assertIn("Source: Crustdata", stdout)

        # Confirm no company names appear in CLI stdout
        forbidden_substrings = [
            "Shandong Sinter",
            "Ningbo Small",
            "Beijing Rare Earth",
            "Hangzhou Large",
            "Zhejiang NdFeB",
            ".example",
            "http://",
        ]
        for sub in forbidden_substrings:
            self.assertNotIn(sub.lower(), stdout.lower())

    def test_cli_shortlist_json_shape(self):
        """CLI --shortlist-json produces schema matching samples/one-item/supplier-shortlist.json."""
        cmd = [sys.executable, "src/discovery/option_c_run.py", "--shortlist-json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, f"CLI exited with error: {proc.stderr}")

        data = json.loads(proc.stdout)
        self.assertEqual(data.get("label"), "SIMULATED")
        self.assertEqual(data.get("mode"), "OFFLINE_FIXTURE_ONLY")
        self.assertIn("item", data)
        self.assertIn("constraints", data)
        self.assertIn("suppliers", data)
        self.assertIn("recommended_label", data)

        self.assertEqual(data["item"]["name"], "neodymium speaker magnet")
        self.assertEqual(data["item"]["thickness_mm"], 3)
        self.assertEqual(data["constraints"]["supplier_country"], "China")
        self.assertEqual(len(data["suppliers"]), 5)
        self.assertEqual(data["suppliers"][0]["label"], "Supplier 1")
        self.assertTrue(len(data["suppliers"][0]["claims"]) > 0)
        self.assertIn("citation", data["suppliers"][0]["claims"][0])
        self.assertIn("[SIMULATED fixture; no live Crustdata call]", data["suppliers"][0]["claims"][0]["citation"])

    def test_live_path_fails_closed_without_api_key(self):
        """--live must fail closed with CrustdataAPIError if no key is configured."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.discovery.option_c_run.load_api_key_from_env", return_value=None):
                with self.assertRaises(CrustdataAPIError):
                    run_one_item_discovery(live=True)

    def test_live_path_fails_closed_when_insufficient_credits(self):
        """Live path pre-flight check halts before calling search if balance is below estimate."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.get_account_credits.return_value = {"account": {"credits": 0.05}}

        with patch("src.discovery.option_c_run.load_api_key_from_env", return_value="mock_key_123"):
            with patch("src.discovery.option_c_run.CrustdataClient", return_value=mock_client):
                with self.assertRaises(CrustdataCreditsExhaustedError):
                    run_one_item_discovery(live=True)

        # Zero live searches made
        mock_client.company_search.assert_not_called()

    def test_live_path_mocked_success(self):
        """Mocked live run with adequate balance succeeds and completes pipeline."""
        mock_client = MagicMock(spec=CrustdataClient)
        mock_client.allow_live = True
        mock_client.get_account_credits.return_value = {"account": {"credits": 500.0}}
        mock_client.company_search.return_value = {
            "results": [
                {
                    "name": "Live NdFeB Corp",
                    "domain": "live-ndfeb.com",
                    "year_founded": 2012,
                    "location": "Ningbo, China",
                    "relevance_score": 0.96,
                }
            ]
        }
        mock_client.company_identify.return_value = [{"crustdata_company_id": 998877}]
        mock_client.company_enrich.return_value = {
            "headcount": {"total": 120},
            "locations": {"headquarters": "Ningbo, China"},
            "basic_info": {"description": "Manufacturer of precision neodymium magnets"},
        }

        with patch("src.discovery.option_c_run.load_api_key_from_env", return_value="mock_key_123"):
            with patch("src.discovery.option_c_run.CrustdataClient", return_value=mock_client):
                suppliers = run_one_item_discovery(live=True)

        self.assertEqual(len(suppliers), 1)
        self.assertEqual(suppliers[0]["display_label"], "Supplier 1")
        self.assertEqual(suppliers[0]["product_line_status"], "CONFIRMED")
        mock_client.company_search.assert_called_once()
        mock_client.company_identify.assert_called_once()
        mock_client.company_enrich.assert_called_once()


    def test_screen_display_rejects_private_sentinel_values(self):
        """Feed synthetic supplier with unique sentinels for every private field and assert none appear in screen output."""
        sentinel_supplier = {
            "display_label": "Supplier 1",
            "name_internal": "SECRET_CORP_SENTINEL_XYZ",
            "primary_domain": "secret-domain-sentinel-xyz.example",
            "year_founded": 1999,
            "headquarters_internal": "SECRET_CITY_SENTINEL_XYZ",
            "headcount_total_internal": 987654321,
            "industry": "SECRET_INDUSTRY_SENTINEL_XYZ",
            "product_line_status": "CONFIRMED",
            "sources": [
                {"field": "primary_domain", "endpoint": "POST /company/identify"},
                {"field": "locations.headquarters", "endpoint": "POST /company/enrich"},
            ],
            "confidence": 0.95,
        }
        output = format_screen_display([sentinel_supplier])
        self.assertNotIn("SECRET_CORP_SENTINEL_XYZ", output)
        self.assertNotIn("secret-domain-sentinel-xyz.example", output)
        self.assertNotIn("SECRET_CITY_SENTINEL_XYZ", output)
        self.assertNotIn("987654321", output)
        self.assertNotIn("SECRET_INDUSTRY_SENTINEL_XYZ", output)

    def test_to_shortlist_payload_dynamic_thickness(self):
        """to_shortlist_payload dynamically parses thickness from spec string."""
        req = build_one_item_request(spec="5 mm thick, low MOQ")
        payload = to_shortlist_payload([], req)
        self.assertEqual(payload["item"]["thickness_mm"], 5)

        req_dec = build_one_item_request(spec="2.5 mm precision magnet")
        payload_dec = to_shortlist_payload([], req_dec)
        self.assertEqual(payload_dec["item"]["thickness_mm"], 2.5)

    def test_json_outputs_carry_run_mode_and_simulated_marker_offline(self):
        """Verify that --shortlist-json and --json carry run mode and SIMULATED marker when offline."""
        cmd_shortlist = [sys.executable, "src/discovery/option_c_run.py", "--shortlist-json"]
        proc_s = subprocess.run(cmd_shortlist, capture_output=True, text=True, check=False)
        self.assertEqual(proc_s.returncode, 0)
        data_s = json.loads(proc_s.stdout)
        self.assertEqual(data_s["label"], "SIMULATED")
        self.assertEqual(data_s["mode"], "OFFLINE_FIXTURE_ONLY")

        cmd_json = [sys.executable, "src/discovery/option_c_run.py", "--json"]
        proc_j = subprocess.run(cmd_json, capture_output=True, text=True, check=False)
        self.assertEqual(proc_j.returncode, 0)
        data_j = json.loads(proc_j.stdout)
        self.assertEqual(data_j["label"], "SIMULATED")
        self.assertEqual(data_j["mode"], "OFFLINE_FIXTURE_ONLY")
        self.assertEqual(len(data_j["suppliers"]), 5)

    def test_company_names_locations_headcount_founding_year_absent_from_output(self):
        """Verify that company names, locations, headcount numbers, and founding years are absent from output."""
        suppliers = run_one_item_discovery(live=False)
        screen_output = format_screen_display(suppliers, is_simulated=True)

        req = build_one_item_request()
        shortlist = to_shortlist_payload(suppliers, req, is_simulated=True)
        shortlist_str = json.dumps(shortlist)

        # 1. Company names that must be absent
        forbidden_names = [
            "Shandong Sinter Magnetics",
            "Ningbo Small Magnetics",
            "Beijing Rare Earth Dynamics",
            "Hangzhou Large Magnetics",
            "Zhejiang NdFeB Precision",
            "Alpha Thermal",
            "Bravo Electro",
            "Charlie Sensors",
            "Delta Pyro",
            "Echo Instruments",
        ]
        # 2. Company locations (headquarters / cities / regions) that must be absent from supplier facts
        forbidden_locations = [
            "Shandong",
            "Ningbo",
            "Beijing",
            "Hangzhou",
            "Zhejiang",
            "Mumbai",
            "Pune",
            "Bengaluru",
            "Ahmedabad",
        ]
        # 3. Headcount values that must be absent
        forbidden_headcounts = [
            "350",
            "600",
            "7500",
            "280",
            "201-500",
            "11-50",
            "501-1000",
            "5001-10000",
            "650",
            "150",
            "75",
            "45",
        ]
        # 4. Founding years that must be absent
        forbidden_years = [
            "2011",
            "2004",
            "2003",
            "1990",
            "2000",
            "1976",
            "1980",
            "1952",
            "1977",
            "2012",
        ]

        for text_out, desc in [(screen_output, "screen_output"), (shortlist_str, "shortlist_json")]:
            for name in forbidden_names:
                self.assertNotIn(name.lower(), text_out.lower(), f"Company name '{name}' leaked in {desc}!")
            for loc in forbidden_locations:
                self.assertNotIn(loc.lower(), text_out.lower(), f"Location '{loc}' leaked in {desc}!")
            for hc in forbidden_headcounts:
                self.assertNotIn(hc, text_out, f"Headcount '{hc}' leaked in {desc}!")
            for yr in forbidden_years:
                self.assertNotIn(yr, text_out, f"Founding year '{yr}' leaked in {desc}!")

    def test_shortlist_payload_rejects_non_pcs_unit(self):
        """to_shortlist_payload strictly rejects units other than 'pcs' / 'pieces' (e.g. kg, liters)."""
        req = build_one_item_request(quantity=10, unit="kg")
        with self.assertRaises(ValueError) as ctx:
            to_shortlist_payload([], req)
        self.assertIn("Unsupported unit 'kg'", str(ctx.exception))

        req_meters = build_one_item_request(quantity=100, unit="meters")
        with self.assertRaises(ValueError):
            to_shortlist_payload([], req_meters)

    def test_cli_shortlist_json_rejects_non_pcs_unit(self):
        """CLI --shortlist-json fails with non-zero exit code when given a non-pcs unit (e.g. --unit kg)."""
        cmd = [sys.executable, "src/discovery/option_c_run.py", "--quantity", "10", "--unit", "kg", "--shortlist-json"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Unsupported unit 'kg'", proc.stderr)

    def test_shortlist_payload_cites_actual_sources(self):
        """to_shortlist_payload cites actual sources present on supplier; keeps failed verification explicit."""
        req = build_one_item_request()
        # 1. Enriched supplier
        s_enrich = {
            "display_label": "Supplier 1",
            "product_line_status": "CONFIRMED",
            "confidence": 0.98,
            "sources": [
                {"field": "primary_domain", "endpoint": "POST /company/identify"},
                {"field": "basic_info.description", "endpoint": "POST /company/enrich"},
            ],
        }
        res_enrich = to_shortlist_payload([s_enrich], req, is_simulated=False)
        self.assertEqual(res_enrich["suppliers"][0]["claims"][0]["citation"], "company enrich: description")
        self.assertIn("CONFIRMED", res_enrich["suppliers"][0]["claims"][0]["text"])

        # 2. Identify only (enrich failed)
        s_ident = {
            "display_label": "Supplier 2",
            "product_line_status": "HUMAN_OR_SIMULATED",
            "confidence": 0.5,
            "sources": [
                {"field": "primary_domain", "endpoint": "POST /company/identify"},
            ],
        }
        res_ident = to_shortlist_payload([s_ident], req, is_simulated=False)
        self.assertEqual(res_ident["suppliers"][0]["claims"][0]["citation"], "company identify: primary_domain")
        self.assertIn("Identified", res_ident["suppliers"][0]["claims"][0]["text"])

        # 3. Unverified (no sources)
        s_unverified = {
            "display_label": "Supplier 3",
            "product_line_status": "HUMAN_OR_SIMULATED",
            "confidence": 0.0,
            "sources": [],
        }
        res_unverified = to_shortlist_payload([s_unverified], req, is_simulated=False)
        self.assertEqual(res_unverified["suppliers"][0]["claims"][0]["citation"], "unverified; no sources")

if __name__ == "__main__":
    unittest.main()
