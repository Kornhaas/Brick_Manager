"""
Simple test to verify the testing setup works.
"""

def test_simple():
    """Simple test to verify pytest is working."""
    assert 1 + 1 == 2

def test_imports():
    """Test that we can import Flask and other dependencies."""
    import flask
    import pytest
    assert flask is not None
    assert pytest is not None