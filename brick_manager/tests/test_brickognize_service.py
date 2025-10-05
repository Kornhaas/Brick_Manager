"""
Unit tests for the brickognize_service module.

This test suite validates the functionality of the `get_predictions` method
from the `brickognize_service` module, including:
- Successful API requests and category enrichment.
- Handling API failures, invalid JSON responses, and database lookup errors.
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import requests
from brick_manager.services.brickognize_service import get_predictions


class TestBrickognizeService(unittest.TestCase):
    """
    Unit tests for the `brickognize_service` module.
    """

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    @patch("requests.post")
    @patch("brick_manager.services.brickognize_service.get_category_name_from_part_num")
    def test_get_predictions_success(self, mock_get_category, mock_post, mock_open_obj):
        """
        Test get_predictions when the API request and category enrichment succeed.
        """
        # Mock the API response
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"items": [{"id": "3001", "confidence": 0.95}]},
        )

        # Mock the category name lookup
        mock_get_category.return_value = "Bricks"

        # Call the function
        file_path = "test_image.jpg"
        filename = "image.jpg"
        result = get_predictions(file_path, filename)

        # Assert the API was called
        mock_post.assert_called_once_with(
            "https://api.brickognize.com/predict/",
            headers={"accept": "application/json"},
            files={"query_image": (
                filename, mock_open_obj(), "image/jpeg")},  # Use the mock file object here
            timeout=10,
        )

        # Assert the database lookup was called
        mock_get_category.assert_called_once_with("3001")

        # Validate the result
        self.assertIsNotNone(result)
        self.assertIn("items", result)
        self.assertEqual(result["items"][0]["category_name"], "Bricks")

        
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    @patch("requests.post")
    def test_get_predictions_api_failure(self, mock_post, _):
        """
        Test get_predictions when the API request fails.
        """
        # Mock an API error
        mock_post.side_effect = requests.exceptions.RequestException(
            "API Error")

        # Call the function
        file_path = "test_image.jpg"
        filename = "image.jpg"
        result = get_predictions(file_path, filename)

        # Assert the API was called
        mock_post.assert_called_once()

        # Validate the result
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    @patch("requests.post")
    def test_get_predictions_invalid_json(self, mock_post, _):
        """
        Test get_predictions when the API returns invalid JSON.
        """
        # Mock a response with invalid JSON
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: None
        )
        mock_post.return_value.json.side_effect = ValueError("Invalid JSON")

        # Call the function
        file_path = "test_image.jpg"
        filename = "image.jpg"
        result = get_predictions(file_path, filename)

        # Assert the API was called
        mock_post.assert_called_once()

        # Validate the result
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data=b"fake_image_data")
    @patch("requests.post")
    @patch("brick_manager.services.brickognize_service.get_category_name_from_part_num")
    def test_get_predictions_db_failure(self, mock_get_category, mock_post, _):
        """
        Test get_predictions when the database category lookup fails.
        """
        # Mock the API response
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"items": [{"id": "3001", "confidence": 0.95}]},
        )

        # Mock a database error
        mock_get_category.side_effect = Exception("DB Error")

        # Call the function
        file_path = "test_image.jpg"
        filename = "image.jpg"
        result = get_predictions(file_path, filename)

        # Assert the API was called
        mock_post.assert_called_once()

        # Validate the result
        self.assertIsNotNone(result)
        self.assertIn("items", result)
        self.assertEqual(result["items"][0]
                         ["category_name"], "Unknown Category")


if __name__ == "__main__":
    unittest.main()
