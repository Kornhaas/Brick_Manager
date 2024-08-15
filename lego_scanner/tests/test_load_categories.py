"""
Unit tests for the load_categories route in the LEGO Scanner Flask application.
"""

import unittest
from unittest.mock import patch
from flask import url_for
from flask_testing import TestCase
import requests
from sqlalchemy.exc import SQLAlchemyError
from app import app, db

class TestLoadCategories(TestCase):
    """
    Test cases for loading and updating LEGO part categories.
    """

    def create_app(self):
        """
        Create the Flask app with testing configuration.
        """
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'supersecretkey'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

    def setUp(self):
        """
        Set up the database before each test.
        """
        db.create_all()

    def tearDown(self):
        """
        Tear down the database after each test.
        """
        db.session.remove()
        db.drop_all()

    @patch('routes.load_categories.get_all_category_ids_from_api')
    def test_load_categories_request_exception(self, mock_get_categories):
        """
        Test handling of a RequestException during category loading.
        """
        mock_get_categories.side_effect = requests.exceptions.RequestException('Network error')

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(b'<!-- index.html -->', response.data)

    @patch('routes.load_categories.get_all_category_ids_from_api')
    @patch('routes.load_categories.db.session.commit')
    def test_load_categories_sqlalchemy_exception(self, mock_db_commit, mock_get_categories):
        """
        Test handling of an SQLAlchemyError during database commit.
        """
        mock_get_categories.return_value = [(1, 'Category 1'), (2, 'Category 2')]
        mock_db_commit.side_effect = SQLAlchemyError('Database error')

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(b'<!-- index.html -->', response.data)

    @patch('routes.load_categories.get_all_category_ids_from_api')
    def test_load_categories_success(self, mock_get_categories):
        """
        Test successful loading and updating of categories.
        """
        mock_get_categories.return_value = [(1, 'Category 1'), (2, 'Category 2')]

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(b'<!-- index.html -->', response.data)

    @patch('routes.load_categories.get_all_category_ids_from_api')
    @patch('routes.load_categories.db.session.commit')
    def test_load_categories_unexpected_exception(self, mock_db_commit, mock_get_categories):
        """
        Test handling of an unexpected exception during database commit.
        """
        mock_get_categories.return_value = [(1, 'Category 1'), (2, 'Category 2')]
        mock_db_commit.side_effect = Exception('Unexpected error')

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(b'<!-- index.html -->', response.data)

if __name__ == '__main__':
    unittest.main()
