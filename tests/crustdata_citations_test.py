"""Tests for demo_citations script."""

import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.discovery.demo_citation import run_demo


class TestDemoCitationScript(unittest.TestCase):

    def test_run_demo_executes_successfully(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_log_path = tf.name

        try:
            captured_out = io.StringIO()
            with patch("sys.stdout", captured_out):
                status = run_demo(log_file=temp_log_path)

            self.assertEqual(status, 0)
            output = captured_out.getvalue()
            self.assertIn("CONTEXTCON 04 - DEMO CITATION RUNNER", output)
            self.assertIn("[Supplier 1]", output)
            self.assertIn("Option C Verification: PASSED", output)
            self.assertIn("Internal audit log saved to:", output)

            # Assert zero real company names or metrics in stdout
            for forbidden in ["Tempsens", "Radix", "Baumer", "Pyrosales", "Sensorcon", "tempsens.com", "radix.co.in"]:
                self.assertNotIn(forbidden.lower(), output.lower(), f"Leaked real name/value to stdout: {forbidden}")

            # Verify internal audit log was actually written to the file
            with open(temp_log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            self.assertIn("Tempsens Instruments", log_content)
        finally:
            if os.path.exists(temp_log_path):
                os.remove(temp_log_path)


if __name__ == "__main__":
    unittest.main()
