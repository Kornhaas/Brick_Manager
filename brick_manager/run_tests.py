"""

Test runner script for comprehensive test coverage.


This script runs all tests and generates coverage reports.
"""

import os
import sys

import pytest

# Add the brick_manager directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_tests():
    """Run all tests with coverage reporting."""

    args = [
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-v",
        "--tb=short",
        "tests/",
    ]

    exit_code = pytest.main(args)
    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    print(f"\nTests completed with exit code: {exit_code}")
    print("Coverage report available in htmlcov/index.html")
    sys.exit(exit_code)
