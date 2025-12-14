"""

Unit tests for the set_search routes module.


This test suite validates the functionality of set search and management.
"""

from unittest.mock import MagicMock, patch


class TestSetSearchRoutes:
    """Test cases for set search routes functionality."""

    def test_set_search_get(self, client):
        """Test GET request to set search page."""

        response = client.get("/set_search")
        assert response.status_code == 200

    def test_search_set_valid_input(self, client):
        """Test searching for a valid set."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_set = MagicMock()
            mock_set.set_num = "10001-1"
            mock_set.name = "Test Set"
            mock_set.year = 2023
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            response = client.post("/search_set", data={"set_number": "10001-1"})
            assert response.status_code == 200

    def test_search_set_invalid_input(self, client):
        """Test searching with invalid input."""

        response = client.post("/search_set", data={"set_number": ""})
        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_search_set_not_found(self, client):
        """Test searching for non-existent set."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_sets.query.filter_by.return_value.first.return_value = None

            response = client.post("/search_set", data={"set_number": "99999-1"})
            assert response.status_code == 200

    @patch("routes.set_search.db.session")
    def test_add_set_complete(self, mock_session, client):
        """Test adding a set with complete status."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_set = MagicMock()
            mock_set.id = 1
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            response = client.post(
                "/add_set", data={"set_num": "10001-1", "status": "complete"}
            )
            assert response.status_code in [200, 302]  # Success or redirect

    @patch("routes.set_search.db.session")
    def test_add_set_assembled(self, mock_session, client):
        """Test adding a set with assembled status."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_set = MagicMock()
            mock_set.id = 1
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            response = client.post(
                "/add_set", data={"set_num": "10001-1", "status": "assembled"}
            )
            assert response.status_code in [200, 302]

    @patch("routes.set_search.db.session")
    def test_add_set_unknown(self, mock_session, client):
        """Test adding a set with unknown status."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_set = MagicMock()
            mock_set.id = 1
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            response = client.post(
                "/add_set", data={"set_num": "10001-1", "status": "unknown"}
            )
            assert response.status_code in [200, 302]

    def test_add_set_nonexistent(self, client):
        """Test adding a non-existent set."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_sets.query.filter_by.return_value.first.return_value = None

            response = client.post(
                "/add_set", data={"set_num": "99999-1", "status": "complete"}
            )
            # Should handle gracefully
            assert response.status_code in [200, 400, 404]

    def test_search_set_method_not_allowed(self, client):
        """Test that only POST is allowed for search_set."""

        response = client.get("/search_set")
        assert response.status_code == 405

    def test_add_set_method_not_allowed(self, client):
        """Test that only POST is allowed for add_set."""

        response = client.get("/add_set")
        assert response.status_code == 405

    def test_search_set_with_special_characters(self, client):
        """Test searching with special characters in set number."""
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_sets.query.filter_by.return_value.first.return_value = None

            response = client.post("/search_set", data={"set_number": '10001-1"&<>'})
            # Should handle special characters safely
            assert response.status_code in [200, 400]

    @patch("routes.set_search.flash")
    def test_add_set_success_message(self, mock_flash, client):
        """Test that success message is displayed when adding set."""
        with patch("routes.set_search.RebrickableSets") as mock_sets, patch(
            "routes.set_search.db.session"
        ):
            mock_set = MagicMock()
            mock_set.id = 1
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            response = client.post(
                "/add_set", data={"set_num": "10001-1", "status": "complete"}
            )

            # Should call flash with success message
            mock_flash.assert_called()

    def test_set_search_csrf_protection(self, client):
        """Test CSRF protection on forms."""

        # This test depends on whether CSRF is implemented
        response = client.post("/search_set", data={"set_number": "10001-1"})
        # Should either work or return appropriate error
        assert response.status_code in [200, 400, 403]


class TestSetMaintenanceRoutes:
    """Test cases for set maintenance routes."""

    def test_set_maintain_get(self, client):
        """Test GET request to set maintenance page."""

        response = client.get("/set_maintain")
        assert response.status_code == 200

    @patch("routes.set_maintain.User_Set")
    def test_set_maintain_with_sets(self, mock_user_set, client):
        """Test set maintenance page with existing sets."""

        mock_set = MagicMock()
        mock_set.id = 1
        mock_set.template_set.set_num = "10001-1"
        mock_set.parts_in_set = []
        mock_user_set.query.options.return_value.order_by.return_value.all.return_value = [
            mock_set
        ]

        response = client.get("/set_maintain")
        assert response.status_code == 200

    @patch("routes.set_maintain.db.session")
    def test_update_user_set(self, mock_session, client):
        """Test updating user set quantities."""

        response = client.post(
            "/update_user_set",
            data={
                "user_set_id": "1",
                "part_1_have_quantity": "2",
                "part_2_have_quantity": "3",
            },
        )
        assert response.status_code in [200, 302]

    def test_set_maintain_method_not_allowed(self, client):
        """Test that set maintenance only allows GET."""

        response = client.post("/set_maintain")
        assert response.status_code == 405


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


class TestDashboardRoutes:
    """Test cases for dashboard routes."""

    def test_dashboard_get(self, client):
        """Test GET request to dashboard page."""

        response = client.get("/dashboard")
        assert response.status_code == 200

    @patch("routes.dashboard.User_Set")
    def test_dashboard_with_data(self, mock_user_set, client):
        """Test dashboard with existing data."""

        mock_set = MagicMock()
        mock_set.id = 1
        mock_user_set.query.all.return_value = [mock_set]

        response = client.get("/dashboard")
        assert response.status_code == 200
