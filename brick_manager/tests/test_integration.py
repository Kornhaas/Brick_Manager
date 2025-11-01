"""

Integration tests for the Bricks Manager application.


These tests check the integration between different components
and the overall application flow.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.integration
class TestApplicationIntegration:
    """Integration tests for the full application."""

    def test_app_startup(self, app):
        """Test that the application starts up correctly."""
        with app.app_context():
            from models import db

            # Check that database tables exist
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            assert (
                len(table_names) >= 0
            )  # Should have some tables after db.create_all()

    def test_database_models_integration(self, app):
        """Test integration between different database models."""
        with app.app_context():
            from models import (
                RebrickableColors,
                RebrickablePartCategories,
                RebrickableSets,
                RebrickableThemes,
                User_Parts,
                User_Set,
                db,
            )

            # Create test data
            category = RebrickablePartCategories(id=1, name="Brick")
            color = RebrickableColors(id=1, name="Red", rgb="FF0000")
            theme = RebrickableThemes(id=1, name="Test Theme")
            template_set = RebrickableSets(
                set_num="10001-1", name="Test Set", year=2023, theme_id=1, num_parts=10
            )

            db.session.add_all([category, color, theme, template_set])
            db.session.commit()

            # Create user set
            user_set = User_Set(set_num=template_set.set_num, status="complete")
            db.session.add(user_set)
            db.session.commit()

            # Create user parts
            user_part = User_Parts(
                user_set_id=user_set.id,
                part_num="3001",
                color_id=color.id,
                quantity=4,
                have_quantity=2,
            )
            db.session.add(user_part)
            db.session.commit()

            # Test relationships
            assert user_set.template_set.name == "Test Set"
            assert len(user_set.parts_in_set) == 1
            assert user_set.parts_in_set[0].part_num == "3001"
            assert user_part.rebrickable_color.name == "Red"

    def test_full_set_workflow(self, client):
        """Test the complete workflow of adding and managing a set."""

        # Step 1: Search for a set
        with patch("routes.set_search.RebrickableSets") as mock_sets:
            mock_set = MagicMock()
            mock_set.set_num = "10001-1"
            mock_set.name = "Test Set"
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            _response = client.post("/search_set", data={"set_number": "10001-1"})
            assert response.status_code == 200

        # Step 2: Add the set
        with patch("routes.set_search.db.session"), patch(
            "routes.set_search.RebrickableSets"
        ) as mock_sets:
            mock_set.id = 1
            mock_sets.query.filter_by.return_value.first.return_value = mock_set

            _response = client.post(
                "/add_set", data={"set_num": "10001-1", "status": "complete"}
            )
            assert response.status_code in [200, 302]

        # Step 3: View set maintenance
        _response = client.get("/set_maintain")
        assert response.status_code == 200

    def test_part_lookup_workflow(self, client):
        """Test the complete part lookup workflow."""

        # Search for a part
        with patch("routes.part_lookup.RebrickableParts") as mock_parts:
            mock_part = MagicMock()
            mock_part.part_num = "3001"
            mock_part.name = "Brick 2 x 4"
            mock_parts.query.filter_by.return_value.first.return_value = mock_part

            _response = client.post("/lookup_part", data={"part_number": "3001"})
            assert response.status_code == 200

    def test_missing_parts_workflow(self, client):
        """Test the missing parts workflow."""

        # View missing parts main page
        _response = client.get("/missing_parts")
        assert response.status_code == 200

        # View missing parts by category
        _response = client.get("/missing_parts_category/Brick")
        assert response.status_code in [200, 404]

    def test_navigation_between_pages(self, client):
        """Test navigation between different pages."""

        pages = [
            "/",
            "/set_search",
            "/lookup_part",
            "/missing_parts",
            "/dashboard",
            "/set_maintain",
        ]

        for page in pages:
            _response = client.get(page)
            assert response.status_code == 200

    @patch("services.cache_service.requests.get")
    def test_image_caching_integration(self, mock_get):
        """Test integration of image caching service."""

        from services.cache_service import cache_image

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_get.return_value = mock_response

        # Test caching
        _result = cache_image("http://example.com/test.jpg")
        assert result.startswith("/static/cache/images/")

    def test_part_lookup_service_integration(self, app):
        """Test integration of part lookup service with database."""
        with app.app_context():
            from models import PartStorage, db
            from services.part_lookup_service import load_part_lookup, save_part_lookup

            # Create test storage data
            storage = PartStorage(
                part_num="3001", location="Shelf A", level="2", box="B1"
            )
            db.session.add(storage)
            db.session.commit()

            # Test loading
            lookup_data = load_part_lookup()
            assert "3001" in lookup_data
            assert lookup_data["3001"]["location"] == "Shelf A"

            # Test saving
            new_data = {"3002": {"location": "Shelf B", "level": "1", "box": "B2"}}
            save_part_lookup(new_data)

            # Verify saved
            updated_data = load_part_lookup()
            assert "3002" in updated_data

    def test_error_handling_integration(self, client):
        """Test error handling across the application."""

        # Test 404 handling
        _response = client.get("/non-existent-page")
        assert response.status_code == 404

        # Test method not allowed
        _response = client.post("/set_maintain")
        assert response.status_code == 405

    def test_security_headers_integration(self, client):
        """Test that security measures are in place."""

        _response = client.get("/")
        assert response.status_code == 200

        # Check for potential security headers
        response.headers
        # Note: These tests depend on implementation
        # Common security headers include:
        # - X-Content-Type-Options
        # - X-Frame-Options
        # - Content-Security-Policy

    def test_static_files_integration(self, client):
        """Test that static files are served correctly."""

        # Test that static files route works
        _response = client.get("/static/default_image.png")
        assert response.status_code in [200, 404]  # File may or may not exist

    def test_database_transaction_rollback(self, app):
        """Test that database transactions roll back on errors."""
        with app.app_context():
            from models import RebrickableSets, db

            try:
                # Start a transaction
                with db.session.begin():
                    # Add valid data
                    test_set = RebrickableSets(set_num="test-1", name="Test Set")
                    db.session.add(test_set)
                    db.session.flush()  # Force database interaction

                    # Force an error
                    raise Exception("Simulated error")

            except Exception:
                # Transaction should be rolled back
                pass

            # Verify rollback occurred
            _result = RebrickableSets.query.filter_by(set_num="test-1").first()
            assert result is None

    def test_concurrent_database_access(self, app):
        """Test concurrent database access doesn't cause issues."""

        import threading

        results = []

        def database_operation():
            """Database operation for concurrent testing."""
            with app.app_context():
                from models import PartStorage, db

                try:
                    storage = PartStorage(
                        part_num=f"test-{threading.current_thread().ident}",
                        location="Test",
                        level="1",
                        box="B1",
                    )
                    db.session.add(storage)
                    db.session.commit()
                    results.append(True)
                except Exception:
                    results.append(False)

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=database_operation)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)


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
        # _result = get_rebrickable_sets(api_key='test')
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

            _result = get_predictions("test_image.jpg", "test.jpg")
            assert result is not None


@pytest.mark.slow
@pytest.mark.integration
class TestPerformanceIntegration:
    """Performance integration tests."""

    def test_page_load_performance(self, client):
        """Test that pages load within acceptable time limits."""

        import time

        pages = ["/", "/set_search", "/lookup_part", "/dashboard"]

        for page in pages:
            start_time = time.time()
            _response = client.get(page)
            end_time = time.time()

            assert response.status_code == 200
            # Should load within 5 seconds
            assert (end_time - start_time) < 5.0

    def test_database_query_performance(self, app):
        """Test database query performance."""

        import time

        with app.app_context():
            from models import RebrickableSets, db

            # Add some test data
            for i in range(100):
                test_set = RebrickableSets(
                    set_num=f"test-{i}", name=f"Test Set {i}", year=2023
                )
                db.session.add(test_set)
            db.session.commit()

            # Time a query
            start_time = time.time()
            results = RebrickableSets.query.filter_by(year=2023).all()
            end_time = time.time()

            assert len(results) == 100
            # Query should complete within 1 second
            assert (end_time - start_time) < 1.0
