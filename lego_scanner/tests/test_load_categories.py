import unittest
from unittest.mock import patch
from flask import url_for
from flask_testing import TestCase
import requests
from sqlalchemy.exc import SQLAlchemyError
from app import app, db
from models import Category

class TestLoadCategories(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        # Set the secret key for session management
        app.config['SECRET_KEY'] = 'supersecretkey'
        # Use in-memory database for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('routes.load_categories.get_all_category_ids_from_api')
    def test_load_categories_request_exception(self, mock_get_categories):
        # Mock the response of get_all_category_ids_from_api to raise a RequestException
        mock_get_categories.side_effect = requests.exceptions.RequestException('Network error')

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)  # follow_redirects=True is key
            self.assertIn(
                b'<!-- index.html -->', response.data)

    @patch('routes.load_categories.get_all_category_ids_from_api')
    @patch('routes.load_categories.db.session.commit')
    def test_load_categories_sqlalchemy_exception(self, mock_db_commit, mock_get_categories):
        # Mock the response of get_all_category_ids_from_api
        mock_get_categories.return_value = [
            (1, 'Category 1'), (2, 'Category 2')]
        # Mock db.session.commit to raise an SQLAlchemyError
        mock_db_commit.side_effect = SQLAlchemyError('Database error')

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(
                b'<!-- index.html -->', response.data)

    @patch('routes.load_categories.get_all_category_ids_from_api')
    def test_load_categories_success(self, mock_get_categories):
        # Mock the response of get_all_category_ids_from_api
        mock_get_categories.return_value = [
            (1, 'Category 1'), (2, 'Category 2')]

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(
                b'<!-- index.html -->', response.data)

    @patch('routes.load_categories.get_all_category_ids_from_api')
    @patch('routes.load_categories.db.session.commit')
    def test_load_categories_unexpected_exception(self, mock_db_commit, mock_get_categories):
        # Mock the response of get_all_category_ids_from_api
        mock_get_categories.return_value = [
            (1, 'Category 1'), (2, 'Category 2')]
        # Mock db.session.commit to raise an unexpected Exception
        mock_db_commit.side_effect = Exception('Unexpected error')

        with self.client:
            response = self.client.post(
                url_for('load_categories.load_categories'), follow_redirects=True)
            self.assertIn(
                b'<!-- index.html -->', response.data)

if __name__ == '__main__':
    unittest.main()
