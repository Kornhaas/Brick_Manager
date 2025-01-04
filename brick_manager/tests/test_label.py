"""Unit tests for label-related routes in the Brick Manager application."""

import subprocess  # Standard library import
import unittest  # Standard library import
from unittest.mock import patch
from flask import url_for  # Third-party imports
from flask_testing import TestCase
from app import app, db # Local application imports
from routes.label import get_absolute_path, print_pdf, secure_filename # Local application imports


class TestLabelRoutes(TestCase):
    """Test cases for the label creation and printing routes."""

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'supersecretkey'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @patch('routes.label.get_part_details')
    @patch('routes.label.load_part_lookup')
    @patch('routes.label.create_label_image')
    @patch('routes.label.save_image_as_pdf')
    @patch('routes.label.print_pdf')
    # pylint: disable=R0913
    def test_create_label_route_success(self,
                                        mock_print_pdf,
                                        mock_save_image_as_pdf,
                                        mock_create_label_image,
                                        mock_load_part_lookup,
                                        mock_get_part_details):
        """Test successful label creation and printing."""
        mock_get_part_details.return_value = {
            'name': 'Test Part',
            'part_img_url': 'http://example.com/image.jpg',
            'part_cat_id': 1
        }
        mock_load_part_lookup.return_value = {'123': {'box': 'Test Box'}}
        mock_create_label_image.return_value = 'fake_image_path'
        mock_save_image_as_pdf.return_value = 'fake_pdf_path'
        mock_print_pdf.return_value = True

        with self.client:
            response = self.client.get(
                url_for('label.create_label_route', part_id='123'))
            self.assertEqual(response.status_code, 302)
            # self.assertEqual(response.location, url_for('main.index'))

    @patch('routes.label.os.path.abspath')
    def test_get_absolute_path(self, mock_abspath):
        """Test that the get_absolute_path function returns the correct absolute path."""
        mock_abspath.return_value = '/absolute/path/to/file'
        result = get_absolute_path('relative/path')
        mock_abspath.assert_called_with('relative/path')
        self.assertEqual(result, '/absolute/path/to/file')

    @patch('routes.label.os.path.exists')
    @patch('routes.label.subprocess.run')
    def test_print_pdf_failure(self, mock_path_exists, mock_subprocess_run):
        """Test handling of a failure when attempting to print a PDF."""
        mock_path_exists.return_value = True
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            1, 'fake_command')
        result = print_pdf('fake_pdf_path')
        self.assertFalse(result)

    def test_secure_filename(self):
        """Test that the secure_filename function sanitizes filenames correctly."""
        filename = 'some/unsafe\\file..name with spaces.pdf'
        result = secure_filename(filename)
        self.assertEqual(result, 'someunsafefilename_with_spaces.pdf')

    @patch('routes.label.get_part_details')
    @patch('routes.label.load_part_lookup')
    def test_create_label_route_no_part_details(self,
                                                mock_load_part_lookup,
                                                mock_get_part_details):
        """Test create_label_route when no part details are returned."""
        mock_get_part_details.return_value = None
        mock_load_part_lookup.return_value = {}

        with self.client:
            response = self.client.get(
                url_for('label.create_label_route', part_id='123'))
            self.assertEqual(response.status_code, 302)
            # self.assertEqual(response.location, url_for('main.index'))

    @patch('routes.label.load_part_lookup')
    @patch('routes.label.get_part_details')
    def test_create_label_route_no_image_url(self, mock_get_part_details, mock_load_part_lookup):
        """Test create_label_route when part details do not include an image URL."""
        mock_get_part_details.return_value = {
            'name': 'Test Part',
            'part_img_url': None,
            'part_cat_id': 1
        }
        mock_load_part_lookup.return_value = {'123': {'box': 'Test Box'}}

        with self.client:
            response = self.client.get(
                url_for('label.create_label_route', part_id='123'))
            self.assertEqual(response.status_code, 200)
            # self.assertEqual(response.location, url_for('main.index'))

    @patch('routes.label.load_part_lookup')
    @patch('routes.label.get_part_details')
    def test_create_label_route_no_box_info(self, mock_get_part_details, mock_load_part_lookup):
        """Test create_label_route when the box information is missing."""
        mock_get_part_details.return_value = {
            'name': 'Test Part',
            'part_img_url': 'http://example.com/image.jpg',
            'part_cat_id': 1
        }
        mock_load_part_lookup.return_value = {}  # No box info

        with self.client:
            response = self.client.get(
                url_for('label.create_label_route', part_id='123'))
            self.assertEqual(response.status_code, 200)
            # self.assertEqual(response.location, url_for('main.index'))


if __name__ == '__main__':
    unittest.main()
