"""Tests for demo_citations script."""

import io
import sys
import unittest
from unittest.mock import patch

from src.discovery.demo_citation import run_demo


class TestDemoCitationScript(unittest.TestCase):

    def test_run_demo_executes_successfully(self):
        captured_out = io.StringIO()
        with patch("sys.stdout", captured_out):
            status = run_demo()

        self.assertEqual(status, 0)
        output = captured_out.getvalue()
        self.assertIn("CONTEXTCON 04 - DEMO CITATION RUNNER", output)
        self.assertIn("[Supplier 1]", output)
        self.assertIn("Option C Verification: PASSED", output)
        self.assertIn("INTERNAL AUDIT LOG", output)


if __name__ == "__main__":
    unittest.main()
