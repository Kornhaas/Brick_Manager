"""

Integration tests for the Bricks Manager application.


These tests check the integration between different components
and the overall application flow.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for external API interactions."""

    @patch("services.rebrickable_service.requests.get")
    def test_rebrickable_api_integration(self, mock_get):
        """Test integration with Rebrickable API service."""

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"set_num": "10001-1", "name": "Test Set", "year": 2023}]
        }
        mock_get.return_value = mock_response

        # This would require the actual service functions to be implemented
        # from services.rebrickable_service import get_rebrickable_sets
        # result = get_rebrickable_sets(api_key='test')
        # assert len(result) == 1

    @patch("services.brickognize_service.requests.post")
    def test_brickognize_api_integration(self, mock_post):
        """Test integration with Brickognize API service."""

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"id": "3001", "confidence": 0.95}]
        }
        mock_post.return_value = mock_response

        # Test the service integration
        from services.brickognize_service import get_predictions

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                b"fake_image"
            )

            result = get_predictions("test_image.jpg", "test.jpg")
            assert result is not None
