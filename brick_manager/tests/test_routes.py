"""

Unit tests for the set_search routes module.


This test suite validates the functionality of set search and management.
"""

from unittest.mock import MagicMock, patch






class TestMissingPartsRoutes:
    """Test cases for missing parts routes."""

    def test_missing_parts_get(self, client):
        """Test GET request to missing parts page."""

        response = client.get("/missing_parts")
        assert response.status_code == 200

    def test_missing_parts_category(self, client):
        """Test missing parts by category."""

        response = client.get("/missing_parts_category/Brick")
        # Should return data or handle gracefully
        assert response.status_code in [200, 404]

    def test_missing_parts_invalid_category(self, client):
        """Test missing parts with invalid category."""

        response = client.get("/missing_parts_category/InvalidCategory")
        assert response.status_code in [200, 404]

    def test_missing_parts_with_special_chars(self, client):
        """Test missing parts category with special characters."""

        response = client.get("/missing_parts_category/Minifig%20Heads")
        assert response.status_code in [200, 404]


class TestPartLookupRoutes:
    """Test cases for part lookup routes."""

    def test_part_lookup_get(self, client):
        """Test GET request to part lookup page."""

        response = client.get("/lookup_part")
        assert response.status_code == 200

    @patch("routes.part_lookup.RebrickableParts")
    def test_part_lookup_valid_part(self, mock_parts, client):
        """Test looking up a valid part."""

        mock_part = MagicMock()
        mock_part.part_num = "3001"
        mock_part.name = "Brick 2 x 4"
        mock_parts.query.filter_by.return_value.first.return_value = mock_part

        response = client.post("/lookup_part", data={"part_number": "3001"})
        assert response.status_code == 200

    def test_part_lookup_invalid_part(self, client):
        """Test looking up an invalid part."""
        with patch("routes.part_lookup.RebrickableParts") as mock_parts:
            mock_parts.query.filter_by.return_value.first.return_value = None

            response = client.post("/lookup_part", data={"part_number": "99999"})
            assert response.status_code == 200
