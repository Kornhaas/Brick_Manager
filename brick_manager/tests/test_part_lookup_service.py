"""
Unit tests for the part_lookup_service module.

This test suite validates the functionality of the part lookup service
including loading and saving part lookup data.
"""

from unittest.mock import MagicMock, patch

import pytest
from services.part_lookup_service import load_part_lookup, save_part_lookup


class TestPartLookupService:
    """Test cases for part_lookup_service functionality."""

    @patch("services.part_lookup_service.PartStorage")
    def test_load_part_lookup_success(self, mock_part_storage):
        """Test successful loading of part lookup data."""
        # Setup
        mock_entry1 = MagicMock()
        mock_entry1.part_num = "3001"
        mock_entry1.location = "Shelf A"
        mock_entry1.level = "2"
        mock_entry1.box = "B1"

        mock_entry2 = MagicMock()
        mock_entry2.part_num = "3002"
        mock_entry2.location = "Shelf B"
        mock_entry2.level = "1"
        mock_entry2.box = "B2"

        mock_part_storage.query.all.return_value = [mock_entry1, mock_entry2]

        # Execute
        result = load_part_lookup()

        # Verify
        expected = {
            "3001": {"location": "Shelf A", "level": "2", "box": "B1"},
            "3002": {"location": "Shelf B", "level": "1", "box": "B2"},
        }
        assert result == expected

    @patch("services.part_lookup_service.PartStorage")
    def test_load_part_lookup_empty(self, mock_part_storage):
        """Test loading part lookup data when no entries exist."""
        # Setup
        mock_part_storage.query.all.return_value = []

        # Execute
        result = load_part_lookup()

        # Verify
        assert result == {}

    @patch("services.part_lookup_service.PartStorage")
    def test_load_part_lookup_with_cache(self, mock_part_storage):
        """Test that caching works properly."""
        # Setup
        mock_entry = MagicMock()
        mock_entry.part_num = "3001"
        mock_entry.location = "Shelf A"
        mock_entry.level = "2"
        mock_entry.box = "B1"

        mock_part_storage.query.all.return_value = [mock_entry]

        # Execute twice
        result1 = load_part_lookup()
        result2 = load_part_lookup()

        # Verify that database was only queried once due to caching
        assert result1 == result2
        mock_part_storage.query.all.assert_called_once()

    @patch("services.part_lookup_service.db")
    @patch("services.part_lookup_service.PartStorage")
    def test_save_part_lookup_new_entries(self, mock_part_storage, mock_db):
        """Test saving new part lookup entries."""
        # Setup
        master_lookup = {
            "3001": {"location": "Shelf A", "level": "2", "box": "B1"},
            "3002": {"location": "Shelf B", "level": "1", "box": "B2"},
        }

        # Mock that no existing entries are found
        mock_part_storage.query.filter_by.return_value.first.return_value = None

        # Execute
        save_part_lookup(master_lookup)

        # Verify
        assert mock_part_storage.call_count == 2  # Two new entries created
        mock_db.session.add.assert_called()
        mock_db.session.commit.assert_called_once()

    @patch("services.part_lookup_service.db")
    @patch("services.part_lookup_service.PartStorage")
    def test_save_part_lookup_update_existing(self, mock_part_storage, mock_db):
        """Test updating existing part lookup entries."""
        # Setup
        master_lookup = {
            "3001": {"location": "Shelf A Updated", "level": "3", "box": "B1"}
        }

        # Mock existing entry
        mock_existing_entry = MagicMock()
        mock_existing_entry.location = "Shelf A"
        mock_existing_entry.level = "2"
        mock_existing_entry.box = "B1"

        mock_part_storage.query.filter_by.return_value.first.return_value = (
            mock_existing_entry
        )

        # Execute
        save_part_lookup(master_lookup)

        # Verify
        assert mock_existing_entry.location == "Shelf A Updated"
        assert mock_existing_entry.level == "3"
        assert mock_existing_entry.box == "B1"
        mock_db.session.commit.assert_called_once()

    @patch("services.part_lookup_service.db")
    @patch("services.part_lookup_service.PartStorage")
    def test_save_part_lookup_mixed_operations(self, mock_part_storage, mock_db):
        """Test saving with both new and existing entries."""
        # Setup
        master_lookup = {
            "3001": {  # Existing entry
                "location": "Shelf A Updated",
                "level": "3",
                "box": "B1",
            },
            "3002": {"location": "Shelf B", "level": "1", "box": "B2"},  # New entry
        }

        # Mock existing entry for 3001, none for 3002
        mock_existing_entry = MagicMock()
        mock_existing_entry.location = "Shelf A"
        mock_existing_entry.level = "2"
        mock_existing_entry.box = "B1"

        def mock_filter_by(part_num):
            if part_num == "3001":
                mock_query = MagicMock()
                mock_query.first.return_value = mock_existing_entry
                return mock_query
            else:
                mock_query = MagicMock()
                mock_query.first.return_value = None
                return mock_query

        mock_part_storage.query.filter_by.side_effect = mock_filter_by

        # Execute
        save_part_lookup(master_lookup)

        # Verify
        assert mock_existing_entry.location == "Shelf A Updated"
        mock_db.session.add.assert_called()  # New entry added
        mock_db.session.commit.assert_called_once()

    def test_save_part_lookup_empty_data(self):
        """Test saving empty part lookup data."""
        # Execute
        save_part_lookup({})

        # Should not raise any errors

    @patch("services.part_lookup_service.db")
    @patch("services.part_lookup_service.PartStorage")
    def test_save_part_lookup_partial_data(self, mock_part_storage, mock_db):
        """Test saving part lookup data with missing fields."""
        # Setup
        master_lookup = {
            "3001": {
                "location": "Shelf A",
                # Missing 'level' and 'box'
            }
        }

        mock_part_storage.query.filter_by.return_value.first.return_value = None

        # Execute
        save_part_lookup(master_lookup)

        # Verify - should handle missing fields gracefully
        mock_db.session.commit.assert_called_once()

    @patch("services.part_lookup_service.db")
    def test_save_part_lookup_database_error(self, mock_db):
        """Test handling database errors during save."""
        # Setup
        master_lookup = {"3001": {"location": "Shelf A"}}
        mock_db.session.commit.side_effect = Exception("Database error")

        # Execute and verify exception is raised
        with pytest.raises(Exception):
            save_part_lookup(master_lookup)

    @patch("services.part_lookup_service.PartStorage")
    def test_load_part_lookup_database_error(self, mock_part_storage):
        """Test handling database errors during load."""
        # Setup
        mock_part_storage.query.all.side_effect = Exception("Database error")

        # Execute and verify exception is raised
        with pytest.raises(Exception):
            load_part_lookup()

    @patch("services.part_lookup_service.PartStorage")
    def test_load_part_lookup_cache_invalidation(self, mock_part_storage):
        """Test that cache is properly invalidated after save."""
        # Setup
        mock_entry = MagicMock()
        mock_entry.part_num = "3001"
        mock_entry.location = "Shelf A"
        mock_entry.level = "2"
        mock_entry.box = "B1"

        mock_part_storage.query.all.return_value = [mock_entry]

        # Execute
        result1 = load_part_lookup()

        # Save new data (should invalidate cache)
        save_part_lookup({"3002": {"location": "Shelf B"}})

        # Load again (should query database again)
        result2 = load_part_lookup()

        # Verify database was queried multiple times
        assert mock_part_storage.query.all.call_count >= 2
