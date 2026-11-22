"""Print-ready box-label PDFs with embedded images and fixed dimensions."""

import hashlib
from contextlib import suppress
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic
from urllib.parse import urlsplit

import reportlab
import requests
from PIL import Image, UnidentifiedImageError
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

# Physical box sizes supplied by the user, in millimeters (length, width, height).
BOX_DIMENSIONS_MM = {
    "MB-1": (160, 110, 50),
    "MB-4": (320, 225, 50),
    "BIG-BOX": (305, 229, 102),
}
SET_LABEL_SIZES = frozenset(BOX_DIMENSIONS_MM)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
IMAGE_WARNING = "Set image unavailable. The PDF contains a placeholder."
_IMAGE_HOSTS = frozenset({"cdn.rebrickable.com", "rebrickable.com"})


@dataclass(frozen=True)
class SetLabelDocument:
    path: Path
    warning: str | None = None


def _write_atomic(destination: Path, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            dir=destination.parent, suffix=".tmp", delete=False
        ) as output:
            temporary = Path(output.name)
            output.write(content)
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _decode_image(content: bytes) -> Image.Image:
    with Image.open(BytesIO(content)) as original:
        if (
            original.format not in {"JPEG", "PNG", "WEBP"}
            or original.width * original.height > MAX_IMAGE_PIXELS
        ):
            raise ValueError("Unsupported catalog image")
        original.thumbnail((2600, 2600), Image.Resampling.LANCZOS)
        rgba = original.convert("RGBA")
        image = Image.new("RGB", rgba.size, "white")
        image.paste(rgba, mask=rgba.getchannel("A"))
        return image


def load_set_image(image_url: str, cache_folder: str | None) -> Image.Image | None:
    """Read one bounded, verified CDN image; redirects/private hosts are rejected."""
    try:
        url = urlsplit(image_url)
        if (
            url.scheme != "https"
            or url.hostname not in _IMAGE_HOSTS
            or url.port not in (None, 443)
            or url.username
            or url.password
        ):
            return None
        cached = None
        if cache_folder:
            cached = (
                Path(cache_folder).resolve()
                / "set_labels"
                / f"{hashlib.sha256(image_url.encode()).hexdigest()}.png"
            )
            if (
                cached.is_file()
                and not cached.is_symlink()
                and cached.stat().st_size <= MAX_IMAGE_BYTES
            ):
                try:
                    return _decode_image(cached.read_bytes())
                except (OSError, ValueError, Image.DecompressionBombError):
                    pass  # Recover a corrupt cache entry with a fresh download.
        deadline = monotonic() + 15
        with requests.get(
            image_url, stream=True, timeout=(3, 10), allow_redirects=False
        ) as response:
            if response.status_code != 200:
                return None
            if int(response.headers.get("Content-Length", "0")) > MAX_IMAGE_BYTES:
                return None
            content = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if (
                    len(content) + len(chunk) > MAX_IMAGE_BYTES
                    or monotonic() > deadline
                ):
                    return None
                content.extend(chunk)
        image = _decode_image(bytes(content))
        if cached is not None:
            encoded = BytesIO()
            image.save(encoded, format="PNG")
            if encoded.tell() <= MAX_IMAGE_BYTES:
                # A read-only cache must not prevent a printable PDF.
                with suppress(OSError):
                    _write_atomic(cached, encoded.getvalue())
        return image
    except (
        requests.RequestException,
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ):
        return None


@lru_cache(maxsize=1)
def _fonts() -> tuple[str, str]:
    # Vera ships with ReportLab, including Alpine; no OS fonts are needed.
    folder = Path(reportlab.__file__).parent / "fonts"
    for name, filename in (("SetLabel", "Vera.ttf"), ("SetLabelBold", "VeraBd.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(folder / filename)))
    return "SetLabel", "SetLabelBold"


def _wrapped(text: str, width: float, font: str, size: float) -> list[str]:
    remaining = " ".join(text.split())
    lines = []
    while remaining:
        end = 1
        while (
            end < len(remaining)
            and pdfmetrics.stringWidth(remaining[: end + 1], font, size) <= width
        ):
            end += 1
        if end < len(remaining):
            space = remaining.rfind(" ", 0, end + 1)
            if space > 0:
                end = space
        lines.append(remaining[:end])
        remaining = remaining[end:].lstrip()
    return lines


def _text(
    pdf: Canvas,
    text: str,
    rect: tuple[float, float, float, float],
    *,
    bold: bool = False,
    size: float = 12,
    min_size: float = 7,
    max_lines: int = 2,
) -> None:
    font = _fonts()[int(bold)]
    x, y, width, height = rect
    while True:
        lines = _wrapped(text, width, font, size)
        if (
            len(lines) <= max_lines and len(lines) * size * 1.2 <= height
        ) or size <= min_size:
            break
        size -= 0.5
    limit = min(max_lines, max(1, int(height / (size * 1.2))))
    if len(lines) > limit:
        lines = lines[:limit]
        last = lines[-1]
        while last and pdfmetrics.stringWidth(last + "…", font, size) > width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    ascent, descent = pdfmetrics.getAscentDescent(font, size)
    leading = size * 1.2
    baseline = y + height / 2 + (len(lines) - 1) * leading / 2 - (ascent + descent) / 2
    pdf.setFont(font, size)
    pdf.setFillColorRGB(0.08, 0.08, 0.08)
    for line in lines:
        pdf.drawCentredString(x + width / 2, baseline, line)
        baseline -= leading


def _photo(
    pdf: Canvas, image: Image.Image | None, rect: tuple[float, float, float, float]
) -> None:
    x, y, width, height = rect
    if image is None:
        _text(pdf, "Image unavailable", rect, size=9)
        return
    scale = min(width / image.width, height / image.height)
    drawn_width, drawn_height = image.width * scale, image.height * scale
    pdf.drawImage(
        ImageReader(image),
        x + (width - drawn_width) / 2,
        y + (height - drawn_height) / 2,
        width=drawn_width,
        height=drawn_height,
    )


def _badge(pdf: Canvas, box_id: int, x: float, y: float) -> None:
    pdf.setFillColorRGB(1, 0.9, 0.8)
    pdf.setStrokeColorRGB(0.65, 0.45, 0.15)
    pdf.setLineWidth(0.4)
    pdf.circle(x, y, 8 * mm, fill=1, stroke=1)
    _text(
        pdf,
        str(box_id),
        (x - 7 * mm, y - 5 * mm, 14 * mm, 10 * mm),
        bold=True,
        size=13,
        min_size=3,
        max_lines=1,
    )


def _outline(pdf: Canvas, width: float, height: float) -> None:
    pdf.setStrokeColorRGB(0.6, 0.6, 0.6)
    pdf.setLineWidth(0.3)
    pdf.rect(0, 0, width, height, fill=0, stroke=1)


def _cover(
    pdf: Canvas,
    image: Image.Image | None,
    box_id: int,
    number: str,
    name: str,
    width: float,
    height: float,
) -> None:
    _outline(pdf, width, height)
    _text(
        pdf,
        f"Bricks Set - {number} - {name}",
        (4 * mm, height - 24 * mm, width - 30 * mm, 20 * mm),
        bold=True,
        size=18 if width > 160 * mm else 13,
        min_size=8,
    )
    _badge(pdf, box_id, width - 13 * mm, height - 13 * mm)
    _photo(pdf, image, (4 * mm, 4 * mm, width - 8 * mm, height - 30 * mm))


def _side(
    pdf: Canvas,
    image: Image.Image | None,
    box_id: int,
    number: str,
    name: str,
    width: float,
    height: float,
    *,
    large: bool = False,
) -> None:
    _outline(pdf, width, height)
    photo_width = (
        min((60 if height <= 40 * mm else 85) * mm, (width - 90 * mm) / 2)
        if large
        else min(width * 0.4, 60 * mm)
    )
    _photo(pdf, image, (4 * mm, 3 * mm, photo_width, height - 6 * mm))
    if large:
        _photo(
            pdf,
            image,
            (width - photo_width - 28 * mm, 3 * mm, photo_width, height - 6 * mm),
        )
        text_x, text_width = photo_width + 10 * mm, width - 2 * photo_width - 42 * mm
    else:
        text_x, text_width = photo_width + 8 * mm, width - photo_width - 32 * mm
    _text(
        pdf,
        number,
        (text_x, height / 2 + 2 * mm, text_width, 12 * mm),
        bold=True,
        size=14,
        min_size=5,
        max_lines=1,
    )
    _text(
        pdf,
        name,
        (text_x, height / 2 - 17 * mm, text_width, 16 * mm),
        size=9,
        min_size=7,
        max_lines=3,
    )
    _badge(pdf, box_id, width - 13 * mm, height - 13 * mm)


def create_set_label_pdf(
    *,
    box_id: int,
    set_number: str,
    set_name: str,
    image_url: str,
    box_size: str,
    output_folder: str,
    cache_folder: str | None = None,
) -> SetLabelDocument:
    """Inset every label by 5 mm; cap large labels to printable A4 landscape."""
    if box_size not in SET_LABEL_SIZES:
        raise ValueError("Unsupported set label size")
    box_length, box_width, box_height = BOX_DIMENSIONS_MM[box_size]
    lid_width, lid_height = min(box_length - 10, 277), min(box_width - 10, 190)
    side_height = box_height - 10
    long_side, short_side = min(box_length - 10, 277), min(box_width - 10, 277)
    image = load_set_image(image_url, cache_folder)
    output = BytesIO()
    pdf = Canvas(output, pagesize=landscape(A4), pageCompression=1)
    pdf.setTitle(f"{box_size} - Box {box_id} - {set_number}")
    pdf.setAuthor("Brick Manager")
    pdf.setViewerPreference("PrintScaling", "None")
    page_width, _ = landscape(A4)

    def footer(page: str) -> None:
        _text(
            pdf,
            f"{box_size} | Box {box_id} | {page} | Print at 100% / actual size",
            (10 * mm, 3 * mm, page_width - 20 * mm, 6 * mm),
            size=8,
            max_lines=1,
        )

    def placed(
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        cover: bool = False,
        rotated: bool = False,
        large: bool = False,
    ) -> None:
        pdf.saveState()
        pdf.translate(x * mm, y * mm)
        if rotated:
            pdf.translate(side_height * mm, 0)
            pdf.rotate(90)
        if cover:
            _cover(pdf, image, box_id, set_number, set_name, width * mm, height * mm)
        else:
            _side(
                pdf,
                image,
                box_id,
                set_number,
                set_name,
                width * mm,
                height * mm,
                large=large,
            )
        pdf.restoreState()

    try:
        if box_size == "MB-1":
            left = (297 - lid_width - 2 * side_height) / 2
            bottom = (210 - lid_height - 2 * side_height) / 2
            placed(
                left + side_height,
                bottom + side_height,
                lid_width,
                lid_height,
                cover=True,
            )
            placed(
                left + side_height,
                bottom + side_height + lid_height,
                long_side,
                side_height,
            )
            placed(left + side_height, bottom, long_side, side_height)
            placed(left, bottom + side_height, short_side, side_height, rotated=True)
            placed(
                left + side_height + lid_width,
                bottom + side_height,
                short_side,
                side_height,
                rotated=True,
            )
            footer("Lid + 4 sides")
        else:
            placed(
                (297 - lid_width) / 2,
                (210 - lid_height) / 2,
                lid_width,
                lid_height,
                cover=True,
            )
            footer(f"Lid - {lid_width} x {lid_height} mm")
            widths = [long_side, long_side, short_side, short_side]
            per_page = int((190 + 5) // (side_height + 5))
            for start in range(0, len(widths), per_page):
                pdf.showPage()
                current = widths[start : start + per_page]
                used_height = len(current) * side_height + (len(current) - 1) * 5
                top = (210 + used_height) / 2 - side_height
                for index, width in enumerate(current):
                    placed(
                        (297 - width) / 2,
                        top - index * (side_height + 5),
                        width,
                        side_height,
                        large=True,
                    )
                footer(
                    f"Sides {start + 1}-{start + len(current)} - {long_side}/{short_side} x {side_height} mm"
                )
        pdf.save()
        destination = Path(output_folder).resolve() / f"{box_id}_{box_size}.pdf"
        _write_atomic(destination, output.getvalue())
        return SetLabelDocument(destination, IMAGE_WARNING if image is None else None)
    finally:
        if image is not None:
            image.close()
