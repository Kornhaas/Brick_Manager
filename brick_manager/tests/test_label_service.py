"""
Unit tests for the label service functions in the Brick Manager application.

This module includes tests for the following functions:
- save_image_as_pdf

These tests use the unittest framework and mock objects for testing image
processing and PDF generation.
"""

import unittest
from unittest.mock import patch, MagicMock
from brick_manager.services.label_service import save_image_as_pdf


class TestLabelService(unittest.TestCase):
    """Unit tests for the label service functions."""

    @patch("brick_manager.services.label_service.Image.open")
    @patch("brick_manager.services.label_service.canvas.Canvas")
    @patch("brick_manager.services.label_service.ImageReader")
    def test_save_image_as_pdf(self, mock_image_reader, mock_canvas, mock_image_open):
        """Test saving an image as a PDF."""
        mock_image = MagicMock()
        mock_image.size = (100, 100)
        mock_image_open.return_value = mock_image
        mock_image_reader.return_value = mock_image

        save_image_as_pdf("fake_image_path", "fake_pdf_path")

        mock_canvas.assert_called_once_with(
            "fake_pdf_path", pagesize=(100, 100))
        self.assertTrue(mock_canvas.return_value.drawImage.called)
        self.assertTrue(mock_canvas.return_value.save.called)


if __name__ == "__main__":
    unittest.main()
