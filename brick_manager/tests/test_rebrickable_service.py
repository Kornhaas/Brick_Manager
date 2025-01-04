"""
Unit tests for the RebrickableService functions.

This module includes tests for the following functions:
- get_part_details
- get_category_name
- get_predictions

These tests use the unittest framework and mock external API calls using the unittest.mock module.
"""
import unittest
from unittest.mock import patch, MagicMock
from services.rebrickable_service import get_part_details, get_category_name, get_predictions

class TestRebrickableService(unittest.TestCase):
    """Unit tests for the RebrickableService functions."""

    @patch('services.rebrickable_service.requests.get')
    def test_get_part_details_success(self, mock_get):
        """Test get_part_details with a valid part number."""
        # Mocking the requests.get response for a successful call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'part_num': '1234', 'name': 'Test Part'}
        mock_get.return_value = mock_response

        result = get_part_details('1234')
        self.assertIsNotNone(result)
        self.assertEqual(result['part_num'], '1234')
        self.assertEqual(result['name'], 'Test Part')

    @patch('services.rebrickable_service.requests.get')
    def test_get_part_details_failure(self, mock_get):
        """Test get_part_details with an invalid part number."""
        # Mocking the requests.get response for a failed call
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_part_details('invalid_part')
        self.assertIsNone(result)

    @patch('services.rebrickable_service.requests.get')
    def test_get_category_name_success(self, mock_get):
        """Test get_category_name with a valid category ID."""
        # Mocking the requests.get response for a successful call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'name': 'Test Category'}
        mock_get.return_value = mock_response

        result = get_category_name('999')
        self.assertEqual(result, 'Test Category')

    @patch('services.rebrickable_service.requests.get')
    def test_get_category_name_failure(self, mock_get):
        """Test get_category_name with an invalid category ID."""
        # Mocking the requests.get response for a failed call
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_category_name('invalid_category')
        self.assertEqual(result, 'Unknown Category')

    @patch('services.rebrickable_service.requests.post')
    def test_get_predictions_success(self, mock_post):
        """Test get_predictions with a valid image upload."""
        # Mocking the requests.post response for a successful call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'predictions': ['Part A', 'Part B']}
        mock_post.return_value = mock_response

        with patch('builtins.open', unittest.mock.mock_open(read_data='image data')):
            result = get_predictions('fake_path.jpg', 'fake_file.jpg')
            self.assertIsNotNone(result)
            self.assertIn('predictions', result)

    @patch('services.rebrickable_service.requests.post')
    def test_get_predictions_failure(self, mock_post):
        """Test get_predictions with a failed image upload."""
        # Mocking the requests.post response for a failed call
        mock_response = MagicMock()
        mock_response.status_code = 400
        # Simulate raising a ValueError when .json() is called
        mock_response.json.side_effect = ValueError("No JSON could be decoded")
        mock_post.return_value = mock_response

        with patch('builtins.open', unittest.mock.mock_open(read_data='image data')):
            result = get_predictions('fake_path.jpg', 'fake_file.jpg')
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
