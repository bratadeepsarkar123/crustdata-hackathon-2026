"""Tests for Option C Screen Display Compliance (Display labels & citations only)."""

import unittest

from src.discovery.service import run_discovery_pipeline, format_screen_display, format_internal_log


class TestCrustdataScreenCompliance(unittest.TestCase):

    def setUp(self):
        self.request = {
            "item": "industrial temperature sensors",
            "quantity": 500,
            "budget": 25000,
            "currency": "USD",
            "deadline_days": 14,
            "region": "India",
            "missing_fields": [],
        }
        self.suppliers = run_discovery_pipeline(self.request, use_fixtures=True)

    def test_screen_display_uses_display_labels_only(self):
        screen_output = format_screen_display(self.suppliers)

        # Must contain display labels
        self.assertIn("[Supplier 1]", screen_output)
        self.assertIn("[Supplier 2]", screen_output)

        # Must cite endpoints and fields
        self.assertIn("Source: Crustdata (POST /company/identify)", screen_output)
        self.assertIn("Source: Crustdata (POST /company/search, field: primary_domain)", screen_output)
        self.assertIn("Source: Crustdata (POST /company/enrich, field: headcount)", screen_output)
        self.assertIn("Source: Crustdata (POST /company/enrich, field: locations)", screen_output)

    def test_screen_display_never_leaks_real_company_names(self):
        screen_output = format_screen_display(self.suppliers)

        forbidden_company_names = [
            "Tempsens",
            "Radix",
            "Baumer",
            "Pyrosales",
            "Sensorcon",
        ]
        for name in forbidden_company_names:
            self.assertNotIn(name.lower(), screen_output.lower(),
                             f"Security violation: Company name '{name}' leaked to screen display!")

    def test_screen_display_never_leaks_company_values(self):
        screen_output = format_screen_display(self.suppliers)

        forbidden_values = [
            "tempsens.com",
            "radix.co.in",
            "baumer.com",
            "650",
            "280",
            "Udaipur",
            "Mumbai",
            "Pune",
        ]
        for val in forbidden_values:
            self.assertNotIn(val.lower(), screen_output.lower(),
                             f"Option C violation: Company value '{val}' leaked to screen display!")

    def test_internal_log_preserves_internal_fields_and_names(self):
        internal_log = format_internal_log(self.suppliers)

        # Internal log MUST preserve real names for audit and policy verification
        self.assertIn("Tempsens Instruments", internal_log)
        self.assertIn("tempsens.com", internal_log)
        self.assertIn("650", internal_log)


if __name__ == "__main__":
    unittest.main()
