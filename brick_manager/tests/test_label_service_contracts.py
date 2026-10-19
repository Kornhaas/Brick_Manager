"""File and image contracts for generated storage labels."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image, ImageFont
from services import label_service


def test_label_output_path_stays_in_upload_directory(tmp_path):
    with patch.object(label_service.Config, "UPLOAD_FOLDER", str(tmp_path)):
        output = Path(
            label_service._label_output_path(
                {"location": "../../outside", "level": "L1", "box": "A/B"},
                "png",
            )
        )

    assert output.parent == tmp_path.resolve()
    assert output.name == "outside_L1_A_B_label.png"


def test_download_image_returns_opened_image_and_handles_http_failure():
    opened = Image.new("RGB", (3, 4))
    successful_response = Mock(raw=object())
    with (
        patch(
            "services.label_service.requests.get", return_value=successful_response
        ) as get,
        patch("services.label_service.Image.open", return_value=opened) as open_image,
    ):
        assert (
            label_service.download_image("https://example.invalid/part.png") is opened
        )
    get.assert_called_once_with(
        "https://example.invalid/part.png", stream=True, timeout=10
    )
    successful_response.raise_for_status.assert_called_once()
    open_image.assert_called_once_with(successful_response.raw)

    with patch("services.label_service.requests.get", side_effect=OSError("offline")):
        assert label_service.download_image("https://example.invalid/part.png") is None
    assert label_service.download_image("") is None


def test_load_fonts_falls_back_to_pillow_default_fonts():
    with (
        patch("services.label_service.ImageFont.truetype", side_effect=OSError),
        patch(
            "services.label_service.ImageFont.load_default", return_value="default"
        ) as load_default,
    ):
        assert label_service.load_fonts() == (
            "default",
            "default",
            "default",
            "default",
        )
    assert load_default.call_count == 4


def test_create_empty_box_label_writes_jpg_inside_configured_directory(tmp_path):
    info = {"location": "hall", "level": "1", "box": "empty", "items": []}
    with patch.object(label_service.Config, "UPLOAD_FOLDER", str(tmp_path)):
        output = Path(label_service.create_box_label_image(info))

    assert output == tmp_path / "hall_1_empty_label.jpg"
    assert output.exists()
    assert Image.open(output).format == "JPEG"


def test_create_box_label_composes_item_images_and_writes_png(tmp_path):
    source_image = Image.new("RGB", (20, 20), color="red")
    info = {
        "location": "hall",
        "level": "1",
        "box": "filled",
        "items": [
            {"part_num": "3001", "category": "Bricks", "img_url": "cached-image"},
            {"part_num": "3002", "category": "Bricks", "img_url": None},
        ],
    }
    with (
        patch.object(label_service.Config, "UPLOAD_FOLDER", str(tmp_path)),
        patch("services.label_service.cache_image", side_effect=lambda value: value),
        patch(
            "services.label_service.download_image", side_effect=[source_image, None]
        ),
        patch(
            "services.label_service.load_fonts",
            return_value=(
                ImageFont.load_default(),
                ImageFont.load_default(),
                ImageFont.load_default(),
                ImageFont.load_default(),
            ),
        ),
    ):
        output = Path(label_service.create_box_label_image(info))

    assert output == tmp_path / "hall_1_filled_label.png"
    assert output.exists()
    assert Image.open(output).format == "PNG"


def test_create_box_label_jpg_converts_and_removes_temporary_png(tmp_path):
    png_path = tmp_path / "temporary.png"
    Image.new("RGB", (10, 10), color="blue").save(png_path)
    with patch(
        "services.label_service.create_box_label_image", return_value=str(png_path)
    ):
        output = Path(label_service.create_box_label_jpg({"box": "converted"}))

    assert output.exists()
    assert output.suffix == ".jpg"
    assert not png_path.exists()
    assert Image.open(output).format == "JPEG"


def test_create_box_label_jpg_requires_generator_output(tmp_path):
    missing_path = tmp_path / "missing.png"
    with (
        patch(
            "services.label_service.create_box_label_image",
            return_value=str(missing_path),
        ),
        pytest.raises(FileNotFoundError, match="Label image not created"),
    ):
        label_service.create_box_label_jpg({"box": "missing"})


def test_create_label_pdf_delegates_and_removes_temporary_image(tmp_path):
    image_path = tmp_path / "label.png"
    image_path.write_bytes(b"placeholder")
    output_path = tmp_path / "label.pdf"
    with (
        patch(
            "services.label_service.create_label_image", return_value=str(image_path)
        ),
        patch("services.label_service.save_image_as_pdf") as save_pdf,
    ):
        assert label_service.create_label_pdf(
            {"item_id": "p1"}, str(output_path)
        ) == str(output_path)

    save_pdf.assert_called_once_with(str(image_path), str(output_path))
    assert not image_path.exists()


def test_storage_label_delegates_to_box_label():
    info = {"box": "delegated"}
    with patch(
        "services.label_service.create_box_label_image", return_value="label.png"
    ) as create:
        assert label_service.create_storage_label(info) == "label.png"
    create.assert_called_once_with(info)
