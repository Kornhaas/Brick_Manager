"""
Unit tests for the LookupService functions.

This module includes tests for the following functions:
- load_part_lookup
- save_part_lookup

These tests use the unittest framework and mock file operations using the unittest.mock module.
"""

import unittest
from unittest.mock import patch, mock_open
from flask import Flask
from brick_manager.services.part_lookup_service import load_part_lookup


class TestLookupService(unittest.TestCase):
    """Unit tests for the lookup service."""

    def setUp(self):
        """Set up a Flask application context for testing."""
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Tear down the Flask application context after testing."""
        self.app_context.pop()

    @patch("builtins.open", new_callable=mock_open, read_data='{"test_key": "test_value"}')
    def test_load_part_lookup(self, mock_file):
        """Test loading the master lookup file."""
        result = load_part_lookup()
        self.assertEqual(result, {"test_key": "test_value"})
        _ = mock_file  # This line is added to avoid the unused argument warning


if __name__ == "__main__":
    unittest.main()
