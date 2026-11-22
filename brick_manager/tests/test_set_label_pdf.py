"""Real PDF geometry, embedded images, bounded downloads, and readable text."""

from io import BytesIO
from math import hypot
from unittest.mock import MagicMock, Mock

import pytest
import requests
from PIL import Image
from pypdf import PdfReader
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from services import set_label_service as labels


def image_bytes(size=(160, 80)):
    output = BytesIO()
    Image.new("RGBA", size, (40, 100, 190, 180)).save(output, format="PNG")
    return output.getvalue()


def remote_response(content=None, *, status=200, headers=None):
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    response.iter_content.return_value = iter(
        [image_bytes() if content is None else content]
    )
    response.__enter__.return_value = response
    return response


def make_pdf(tmp_path, *, size="MB-4", name="Castle Nocturnia", image_url=""):
    return labels.create_set_label_pdf(
        box_id=187,
        set_number="71486-1",
        set_name=name,
        image_url=image_url,
        box_size=size,
        output_folder=str(tmp_path / "output"),
        cache_folder=str(tmp_path / "cache"),
    )


@pytest.mark.parametrize(
    "size,dimensions",
    [
        ("MB-1", [(150, 100), (150, 40), (150, 40), (40, 100), (40, 100)]),
        ("MB-4", [(277, 190), (277, 40), (277, 40), (215, 40), (215, 40)]),
        ("BIG-BOX", [(277, 190), (277, 92), (277, 92), (219, 92), (219, 92)]),
    ],
)
def test_printed_labels_preserve_mm_dimensions_and_stay_inside_paper(
    tmp_path, size, dimensions
):
    reader = PdfReader(make_pdf(tmp_path, size=size).path)
    measured = []
    for page in reader.pages:

        def inspect(operator, operands, cm, _tm, page=page):
            if operator != b"re":
                return
            x, y, width, height = map(float, operands)
            corners = [
                (cm[0] * px + cm[2] * py + cm[4], cm[1] * px + cm[3] * py + cm[5])
                for px, py in (
                    (x, y),
                    (x + width, y),
                    (x, y + height),
                    (x + width, y + height),
                )
            ]
            xs, ys = zip(*corners, strict=True)
            assert min(xs) >= 9 * mm
            assert min(ys) >= 9 * mm
            assert max(xs) <= float(page.mediabox.width) - 9 * mm
            assert max(ys) <= float(page.mediabox.height) - 9 * mm
            measured.append(((max(xs) - min(xs)) / mm, (max(ys) - min(ys)) / mm))

        page.extract_text(visitor_operand_before=inspect)
    assert len(measured) == len(dimensions)
    for actual, expected in zip(measured, dimensions, strict=True):
        assert actual == pytest.approx(expected, abs=0.01)


def test_pdf_embeds_one_cached_image_for_all_formats(tmp_path, monkeypatch):
    response = remote_response()
    download = Mock(return_value=response)
    monkeypatch.setattr(labels.requests, "get", download)
    url = "https://cdn.rebrickable.com/media/sets/71486-1.jpg"
    for size in ("MB-1", "MB-4", "BIG-BOX"):
        result = make_pdf(tmp_path, size=size, image_url=url)
        assert result.warning is None
        assert url.encode() not in result.path.read_bytes()
        for page in PdfReader(result.path).pages:
            assert len(page.images) == 1
            assert page.images[0].image.size == (160, 80)
            assert "Image unavailable" not in page.extract_text()

            def inspect(operator, _operands, cm, _tm):
                if operator == b"Do":
                    assert hypot(cm[0], cm[1]) / hypot(cm[2], cm[3]) == pytest.approx(
                        2, abs=0.001
                    )

            page.extract_text(visitor_operand_before=inspect)
    download.assert_called_once_with(
        url, stream=True, timeout=(3, 10), allow_redirects=False
    )
    response.__exit__.assert_called_once()
    assert len(list((tmp_path / "cache" / "set_labels").glob("*.png"))) == 1


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://cdn.rebrickable.com/a.png",
        "https://127.0.0.1/a.png",
        "file:///etc/passwd",
        "https://example.test/a.png",
        "https://cdn.rebrickable.com.evil.test/a.png",
        "https://user:password@cdn.rebrickable.com/a.png",
        "https://cdn.rebrickable.com:444/a.png",
    ],
)
def test_untrusted_image_location_never_causes_request(tmp_path, monkeypatch, url):
    download = Mock()
    monkeypatch.setattr(labels.requests, "get", download)
    assert labels.load_set_image(url, str(tmp_path)) is None
    download.assert_not_called()


@pytest.mark.parametrize("status", [301, 302, 401, 403, 404, 429, 503])
def test_image_http_failure_is_bounded_placeholder(tmp_path, monkeypatch, status):
    response = remote_response(status=status)
    download = Mock(return_value=response)
    monkeypatch.setattr(labels.requests, "get", download)
    result = make_pdf(tmp_path, image_url="https://cdn.rebrickable.com/media/a.png")
    assert result.warning == labels.IMAGE_WARNING
    assert "Image unavailable" in PdfReader(result.path).pages[0].extract_text()
    download.assert_called_once()
    response.iter_content.assert_not_called()
    response.__exit__.assert_called_once()


@pytest.mark.parametrize("error", [requests.Timeout, requests.ConnectionError])
def test_image_network_failure_still_produces_explained_pdf(
    tmp_path, monkeypatch, error
):
    monkeypatch.setattr(labels.requests, "get", Mock(side_effect=error("unavailable")))
    result = make_pdf(tmp_path, image_url="https://cdn.rebrickable.com/media/a.png")
    assert result.warning == labels.IMAGE_WARNING
    assert len(PdfReader(result.path).pages) == 2


@pytest.mark.parametrize(
    "content,headers",
    [
        (b"not an image", {}),
        (b"small", {"Content-Length": str(labels.MAX_IMAGE_BYTES + 1)}),
        (b"small", {"Content-Length": "invalid"}),
    ],
)
def test_invalid_image_response_never_enters_cache(
    tmp_path, monkeypatch, content, headers
):
    monkeypatch.setattr(
        labels.requests,
        "get",
        Mock(return_value=remote_response(content, headers=headers)),
    )
    assert (
        labels.load_set_image("https://cdn.rebrickable.com/media/a.png", str(tmp_path))
        is None
    )
    assert not list(tmp_path.rglob("*.png"))


def test_stream_size_limit_works_without_content_length(tmp_path, monkeypatch):
    response = remote_response()
    response.iter_content.return_value = iter([b"1234", b"5678"])
    monkeypatch.setattr(labels, "MAX_IMAGE_BYTES", 7)
    monkeypatch.setattr(labels.requests, "get", Mock(return_value=response))
    assert (
        labels.load_set_image("https://cdn.rebrickable.com/media/a.png", str(tmp_path))
        is None
    )
    response.__exit__.assert_called_once()


def test_stream_deadline_stops_a_slow_download(tmp_path, monkeypatch):
    response = remote_response()
    clock = iter([0, 16])
    monkeypatch.setattr(labels, "monotonic", lambda: next(clock))
    monkeypatch.setattr(labels.requests, "get", Mock(return_value=response))
    assert (
        labels.load_set_image("https://cdn.rebrickable.com/media/a.png", str(tmp_path))
        is None
    )
    response.__exit__.assert_called_once()


def test_image_pixel_limit_prevents_decompression_of_large_images(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(labels, "MAX_IMAGE_PIXELS", 10)
    monkeypatch.setattr(labels.requests, "get", Mock(return_value=remote_response()))
    assert (
        labels.load_set_image("https://cdn.rebrickable.com/media/a.png", str(tmp_path))
        is None
    )
    assert not list(tmp_path.rglob("*.png"))


def test_large_box_identifier_is_never_truncated(tmp_path):
    identifier = 2**63 - 1
    result = labels.create_set_label_pdf(
        box_id=identifier,
        set_number="71486-1",
        set_name="Castle Nocturnia",
        image_url="",
        box_size="MB-1",
        output_folder=str(tmp_path),
    )
    text = PdfReader(result.path).pages[0].extract_text()
    # Five badges and the page footer retain the actual identity.
    assert text.count(str(identifier)) == 6


def test_corrupt_cache_is_refreshed_and_read_only_cache_does_not_break_pdf(
    tmp_path, monkeypatch
):
    url = "https://cdn.rebrickable.com/media/a.png"
    monkeypatch.setattr(labels.requests, "get", Mock(return_value=remote_response()))
    labels.load_set_image(url, str(tmp_path)).close()
    cached = next(tmp_path.rglob("*.png"))
    cached.write_bytes(b"broken image")
    monkeypatch.setattr(labels.requests, "get", Mock(return_value=remote_response()))

    def unavailable(*args):
        raise OSError("read-only cache")

    monkeypatch.setattr(labels, "_write_atomic", unavailable)
    image = labels.load_set_image(url, str(tmp_path))
    assert image.size == (160, 80)
    image.close()
    assert cached.read_bytes() == b"broken image"


@pytest.mark.parametrize(
    "name",
    [
        "Sehr großes Schloss mit Ärger & Spaß <Sonderedition>",
        "LongUnbrokenCatalogName" * 14,
    ],
)
def test_long_text_is_fitted_within_its_print_area(name):
    pdf = Mock()
    font = labels._fonts()[1]
    rect = (10 * mm, 20 * mm, 24 * mm, 12 * mm)
    labels._text(pdf, name, rect, bold=True, size=14, min_size=7, max_lines=3)
    actual_font, size = pdf.setFont.call_args.args
    assert actual_font == font
    assert size >= 7
    assert 1 <= pdf.drawCentredString.call_count <= 3
    ascent, descent = pdfmetrics.getAscentDescent(font, size)
    for call in pdf.drawCentredString.call_args_list:
        center, baseline, text = call.args
        width = pdfmetrics.stringWidth(text, font, size)
        assert center - width / 2 >= rect[0] - 0.01
        assert center + width / 2 <= rect[0] + rect[2] + 0.01
        assert baseline + descent >= rect[1]
        assert baseline + ascent <= rect[1] + rect[3]


def test_invalid_pdf_size_is_rejected_before_download(tmp_path, monkeypatch):
    download = Mock()
    monkeypatch.setattr(labels.requests, "get", download)
    with pytest.raises(ValueError, match="Unsupported"):
        make_pdf(tmp_path, size="../unknown")
    download.assert_not_called()
