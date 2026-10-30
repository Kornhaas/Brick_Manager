# pyright: reportMissingModuleSource=false
"""

This module provides functions to create label images and save them as PDFs

for the Brick Manager application.

It includes functionalities to:
- Wrap text to fit within a specified width.
- Generate a label image with part information, including name, image, category, and box number.
- Convert the generated label image to a PDF and save it.
"""

import logging
import os
from io import BytesIO
from pathlib import Path

import requests
from config import Config
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename

from services.cache_service import cache_image  # Import the cache_image function

CM = 28.35  # 1 cm in points
AVERY_3474_COLUMNS = 3
AVERY_3474_ROWS = 8
AVERY_3474_LABELS_PER_PAGE = AVERY_3474_COLUMNS * AVERY_3474_ROWS
AVERY_3474_LABEL_WIDTH = 70 * mm
AVERY_3474_LABEL_HEIGHT = 37 * mm
LABEL_IMAGE_DPI = 300
PDF_POINTS_PER_INCH = 72


def _label_output_path(box_info, extension):
    """Build a label path contained within the configured upload directory."""
    upload_dir = Path(Config.UPLOAD_FOLDER).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    components = [
        secure_filename(str(box_info.get(field, "unknown"))) or "unknown"
        for field in ("location", "level", "box")
    ]
    output_path = (upload_dir / f"{'_'.join(components)}_label.{extension}").resolve()
    if output_path.parent != upload_dir:
        raise ValueError("Invalid label output path")
    return str(output_path)


def download_image(img_url):
    """

    Fetch and open an image from a URL or local cache.


    Args:
        img_url (str): The URL or local path of the image.

    Returns:
        Image: The opened image, or None if the process fails.
    """
    if not img_url:
        return None

    try:
        response = requests.get(img_url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(response.raw)
    except Exception as error:
        logging.error("Error processing image for URL %s: %s", img_url, error)
        return None


def _draw_fitted_text(
    pdf, text, x_position, y_position, max_width, max_size=9, min_size=5
):
    """Draw one line, shrinking and truncating it to the available width."""
    value = str(text or "")
    font_size = max_size
    while (
        font_size > min_size and stringWidth(value, "Helvetica", font_size) > max_width
    ):
        font_size -= 0.5
    while value and stringWidth(value, "Helvetica", font_size) > max_width:
        value = value[:-2].rstrip() + "…"
    pdf.setFont("Helvetica", font_size)
    pdf.drawCentredString(x_position, y_position, value)


def _prepare_pdf_image(source_image, max_width, max_height):
    """Prepare an image at print resolution while returning its size in PDF points."""
    image = source_image.convert("RGBA")
    scale = min(max_width / image.width, max_height / image.height)
    draw_width = image.width * scale
    draw_height = image.height * scale
    max_pixels = (
        max(1, round(draw_width / PDF_POINTS_PER_INCH * LABEL_IMAGE_DPI)),
        max(1, round(draw_height / PDF_POINTS_PER_INCH * LABEL_IMAGE_DPI)),
    )
    if image.width > max_pixels[0] or image.height > max_pixels[1]:
        image.thumbnail(max_pixels, Image.Resampling.LANCZOS)
    return image, draw_width, draw_height


def _draw_avery_3474_label(pdf, box_info, x_position, y_position):
    """Draw one 70 x 37 mm storage-box label into an existing PDF canvas."""
    padding = 3 * mm
    items = box_info.get("items", [])
    visible_items = items[:6]
    item_width = (AVERY_3474_LABEL_WIDTH - 2 * padding) / max(len(visible_items), 1)
    image_height = 13 * mm
    image_y = y_position + AVERY_3474_LABEL_HEIGHT - padding - image_height

    for index, item in enumerate(visible_items):
        center_x = x_position + padding + item_width * (index + 0.5)
        # Use the source URL directly here. Calling the app's own cache URL while
        # generating a response can deadlock a single-worker deployment.
        item_image = download_image(item.get("img_url"))
        if item_image:
            image, draw_width, draw_height = _prepare_pdf_image(
                item_image, item_width * 0.86, image_height
            )
            pdf.drawImage(
                ImageReader(image),
                center_x - draw_width / 2,
                image_y + (image_height - draw_height) / 2,
                width=draw_width,
                height=draw_height,
                mask="auto",
                preserveAspectRatio=True,
            )
        _draw_fitted_text(
            pdf,
            item.get("part_num", "Unknown"),
            center_x,
            y_position + 14 * mm,
            item_width - 1 * mm,
            max_size=8,
        )

    if len(items) > len(visible_items):
        pdf.setFont("Helvetica", 5)
        pdf.drawRightString(
            x_position + AVERY_3474_LABEL_WIDTH - padding,
            y_position + 11.5 * mm,
            f"+{len(items) - len(visible_items)}",
        )

    category = items[0].get("category", "Unknown") if items else "Empty box"
    circle_radius = 4.5 * mm
    circle_x = x_position + AVERY_3474_LABEL_WIDTH - padding - circle_radius
    circle_y = y_position + padding + circle_radius
    category_left = x_position + padding
    category_right = circle_x - circle_radius - 2 * mm
    pdf.setFillColorRGB(0, 0.55, 0.85)
    _draw_fitted_text(
        pdf,
        category,
        (category_left + category_right) / 2,
        y_position + padding + 1 * mm,
        category_right - category_left,
        max_size=9,
    )
    pdf.setFillColorRGB(0, 0, 0)

    pdf.setFillColorRGB(1, 0.85, 0.45)
    pdf.circle(circle_x, circle_y, circle_radius, fill=1, stroke=1)
    pdf.setFillColorRGB(0, 0, 0)
    _draw_fitted_text(
        pdf,
        box_info.get("box", "?"),
        circle_x,
        circle_y - 1.5 * mm,
        8 * mm,
        max_size=10,
    )


def create_avery_3474_pdf(
    boxes, start_position=1, horizontal_offset_mm=0, vertical_offset_mm=0
):
    """Create a print-ready Avery 3474 A4 PDF and return it as a byte stream."""
    if not 1 <= start_position <= AVERY_3474_LABELS_PER_PAGE:
        raise ValueError("Start position must be between 1 and 24")
    if not boxes:
        raise ValueError("At least one box is required")
    if not -10 <= horizontal_offset_mm <= 10 or not -10 <= vertical_offset_mm <= 10:
        raise ValueError("Print offsets must be between -10 and 10 mm")

    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4, pageCompression=1)
    pdf.setTitle(
        f"Avery 3474 box labels (X {horizontal_offset_mm:g} mm, Y {vertical_offset_mm:g} mm)"
    )
    slot = start_position - 1

    for box_info in boxes:
        if slot >= AVERY_3474_LABELS_PER_PAGE:
            pdf.showPage()
            slot = 0

        column = slot % AVERY_3474_COLUMNS
        row = slot // AVERY_3474_COLUMNS
        x_position = column * AVERY_3474_LABEL_WIDTH + horizontal_offset_mm * mm
        y_position = (
            A4[1]
            - 0.5 * mm
            - (row + 1) * AVERY_3474_LABEL_HEIGHT
            - vertical_offset_mm * mm
        )
        _draw_avery_3474_label(pdf, box_info, x_position, y_position)
        slot += 1

    pdf.save()
    output.seek(0)
    return output


def wrap_text(text, font, max_width):
    """

    Wrap the text to fit within the specified maximum width.


    Args:
        text (str): The text to wrap.
        font (ImageFont): The font used for the text.
        max_width (int): The maximum width allowed for the text.

    Returns:
        list: A list of lines that fit within the max_width.
    """
    lines = []

    words = text.split()
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))  # Temporary draw object

    while words:
        line = ""
        while (
            words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width
        ):
            line += words.pop(0) + " "
        lines.append(line)
    return lines


def load_fonts():
    """

    Load fonts for the label.


    Returns:
        tuple: A tuple containing three different font sizes.
    """
    try:
        font = ImageFont.truetype("arial.tt", 16)
        font2 = ImageFont.truetype("arial.tt", 24)
        font3 = ImageFont.truetype("arial.tt", 26)
        font4 = ImageFont.truetype("arial.tt", 10)
    except OSError:
        logging.warning("Font not found. Using default fonts.")
        font = ImageFont.load_default()
        font2 = ImageFont.load_default()
        font3 = ImageFont.load_default()
        font4 = ImageFont.load_default()
    return font, font2, font3, font4


def draw_text(draw, text_info):
    """

    Draw wrapped text on the image.


    Args:
        draw (ImageDraw.Draw): The draw object.
        text_info (dict): A dictionary containing text, position, font, max_width, and y_offset.

    Returns:
        int: The new y position after drawing the text.
    """
    x, y = text_info["position"]

    font = text_info["font"]
    max_width = text_info["max_width"]
    y_offset = text_info.get("y_offset", 0)

    logging.debug(
        "Drawing text: %s at position (%d, %d) with max_width %d",
        text_info["text"],
        x,
        y,
        max_width,
    )

    try:
        lines = wrap_text(text_info["text"], font, max_width)
        logging.debug("Wrapped text into %d lines: %s", len(lines), lines)

        for line in lines:
            draw.text((x, y + y_offset), line, font=font, fill="black")
            y_offset += draw.textbbox((0, 0), line, font=font)[3]
            logging.debug("Rendered line: %s, y_offset now: %d", line, y_offset)

    except Exception as error:
        logging.error("Error rendering text: %s", error)

    return y_offset


def draw_text_dynamic(draw, text_info):
    """

    Draw wrapped text on the image with dynamic font size.


    Args:
        draw (ImageDraw.Draw): The draw object.
        text_info (dict): A dictionary containing text, position, max_width, and y_offset.

    Returns:
        int: The new y position after drawing the text.
    """
    x, y = text_info["position"]

    max_width = text_info["max_width"]
    y_offset = text_info.get("y_offset", 0)
    text = text_info["text"]

    logging.debug(
        "Drawing text: %s at position (%d, %d) with max_width %d", text, x, y, max_width
    )

    base_font_path = "arial.tt"
    max_font_size = 24
    min_font_size = 8

    font_size = max_font_size
    while font_size >= min_font_size:
        try:
            font = ImageFont.truetype(base_font_path, font_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            if bbox[2] <= max_width:
                break
        except Exception as error:
            logging.error("Error loading font at size %d: %s", font_size, error)
            font = ImageFont.load_default()
        font_size -= 1

    logging.debug("Using font size %d for text: %s", font_size, text)

    lines = wrap_text(text, font, max_width)
    logging.debug("Wrapped text into %d lines: %s", len(lines), lines)

    for line in lines:
        bbox = draw.textbbox((x, y + y_offset), line, font=font)
        draw.text((x, y + y_offset), line, font=font, fill="black")
        y_offset += bbox[3] - bbox[1]
        logging.debug("Rendered line: %s, updated y_offset: %d", line, y_offset)

    return y_offset


def create_label_image(label_info):
    """

    Create a label image with part details.


    Args:
        label_info (dict): A dictionary containing label details.

    Returns:
        str: The path to the saved label image.
    """
    logging.info("Creating label for item %s", label_info["item_id"])

    width, height = int(12 * CM), int(8 * CM)
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    font, font2, font3, _ = load_fonts()
    cached_image_url = cache_image(label_info["img_url"])
    item_image = download_image(cached_image_url)

    if item_image:
        item_image.thumbnail((width // 2, height // 2))
        image.paste(item_image, (width // 4, height // 4))
    else:
        logging.warning("No image available for this part")

    draw_text(
        draw,
        {
            "text": label_info["name"],
            "position": (20, 10),
            "font": font2,
            "max_width": width - 40,
        },
    )

    draw.text((15, height - 60), f"{label_info['item_id']}", font=font2, fill="black")
    draw.text(
        (width - 120, height - 60),
        f"Box: {label_info['box']}",
        font=font3,
        fill="black",
    )
    draw.text((50, height - 30), label_info["category"], font=font, fill="blue")

    temp_image_path = os.path.join("uploads", f"label_{label_info['item_id']}.png")
    image.save(temp_image_path, dpi=(300, 300))

    return temp_image_path


def save_image_as_pdf(image_path, pdf_path):
    """

    Save the provided image file as a PDF.


    Args:
        image_path (str): The path to the image file.
        pdf_path (str): The path where the PDF will be saved.
    """
    img = Image.open(image_path)

    img_width, img_height = img.size

    c = canvas.Canvas(pdf_path, pagesize=(img_width, img_height))
    img_reader = ImageReader(image_path)
    c.drawImage(img_reader, 0, 0, width=img_width, height=img_height)
    c.save()
    logging.info("Saved PDF as %s", pdf_path)


def create_box_label_image(box_info):
    """

    Create a label image for a box containing multiple items.


    Args:
        box_info (dict): A dictionary containing box details such as
                         location, level, box, and a list of items.

    Returns:
        str: The path to the saved box label image.
    """
    logging.info(
        "Creating label for box %s at location %s level %s",
        box_info.get("box", "unknown"),
        box_info.get("location", "unknown"),
        box_info.get("level", "unknown"),
    )
    logging.debug("Box info: %s", box_info)

    # Correct label size: 14cm x 7cm
    width, height = int(14 * CM), int(6.5 * CM)
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    font, _, font3, _ = load_fonts()
    items = box_info.get("items", [])
    num_items = len(items)
    logging.debug("Number of items to process: %d", num_items)

    # Handle case with no items
    if num_items == 0:
        logging.warning(
            "No items found in the box %s. Skipping label generation.",
            box_info.get("box"),
        )
        draw.text(
            (width // 2, height // 2),
            "No items available",
            font=font,
            fill="red",
            anchor="mm",
        )
        temp_image_path = _label_output_path(box_info, "jpg")
        image.save(temp_image_path, dpi=(300, 300))
        return temp_image_path

    # Adjusted maximum dimensions for images
    max_image_width = int(width / num_items)
    max_image_height = int(height * 0.4)

    # Spacing for text
    text_y_offset = int(height * 0.45)

    for idx, item in enumerate(items):
        logging.debug(
            "Processing item %d/%d: %s", idx + 1, num_items, item.get("part_num")
        )

        # Use cache_image to get the image URL
        cached_image_url = cache_image(item.get("img_url"))
        item_image = download_image(cached_image_url)

        # Calculate x position for this item
        x_start = idx * (width // num_items)
        x_center = x_start + (max_image_width // 2)

        if item_image:
            logging.debug(
                "Original image size for %s: %s", item.get("part_num"), item_image.size
            )
            item_image.thumbnail((max_image_width, max_image_height))
            logging.debug(
                "Resized image size for %s: %s", item.get("part_num"), item_image.size
            )

            # Center the image in its slot
            x_image_offset = x_center - (item_image.width // 2)
            image.paste(item_image, (x_image_offset, 5))
        else:
            logging.warning("No image available for part %s", item.get("part_num"))

        # Calculate the text width and center the text
        draw_text_dynamic(
            draw,
            {
                "text": item.get("part_num", "Unknown"),
                "position": (x_center - (max_image_width // 2), text_y_offset),
                "max_width": max_image_width,
            },
        )

    # Add the category of the first item at the bottom
    if items:
        first_item_category = items[0].get("category", "No Category")
        category_text_width = draw.textbbox((0, 0), first_item_category, font=font3)[2]
        x_category_offset = (width // 2) - (category_text_width // 2)
        draw.text(
            (x_category_offset, height - 50),  # Position near the bottom
            first_item_category,
            font=font3,
            fill="blue",
        )

    # Add the box number in bold in the bottom-right corner
    box_number_text = f"{box_info.get('box', 'unknown')}"
    box_number_width = draw.textbbox((0, 0), box_number_text, font=font3)[2]
    box_x = width - box_number_width - 10  # Bottom-right corner with padding
    box_y = height - 30

    # Simulate bold text by drawing the same text multiple times with slight offsets
    for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        draw.text(
            (box_x + offset[0], box_y + offset[1]),
            box_number_text,
            font=font3,
            fill="red",
        )

    temp_image_path = _label_output_path(box_info, "png")

    # Save the final composite label as an image
    image.save(temp_image_path, dpi=(300, 300))
    logging.debug("Final label saved: %s", temp_image_path)

    return temp_image_path


def create_box_label_jpg(box_info):
    """

    Generate a JPG label for a box containing multiple items.


    Args:
        box_info (dict): A dictionary containing box details.

    Returns:
        str: The path to the saved JPG file.
    """
    logging.info("Generating JPG label for box %s.", box_info.get("box", "unknown"))

    # Generate the PNG image for the label
    image_path = create_box_label_image(box_info)
    if not os.path.exists(image_path):
        logging.error(
            "Failed to create PNG label image. Path does not exist: %s", image_path
        )
        raise FileNotFoundError(f"Label image not created: {image_path}")

    # Prepare JPG file path
    jpg_path = os.path.splitext(image_path)[0] + ".jpg"

    # Convert PNG to JPG
    try:
        with Image.open(image_path) as img:
            rgb_image = img.convert("RGB")
            rgb_image.save(jpg_path, "JPEG", quality=95)
            logging.info("JPG file created: %s", jpg_path)
    except Exception as e:
        logging.error("Error converting PNG to JPG: %s", e)
        raise

    # Remove temporary PNG file
    if os.path.exists(image_path):
        os.remove(image_path)
    else:
        logging.warning("Temporary PNG file not found for deletion: %s", image_path)

    # Validate JPG creation and return
    if not os.path.exists(jpg_path):
        logging.error(
            "Failed to create JPG label image. Path does not exist: %s", jpg_path
        )
        raise FileNotFoundError(f"JPG label image not created: {jpg_path}")

    return jpg_path


def generate_qr_code(data, size=100):
    """

    Generate a QR code for the given data.


    Args:
        data (str): Data to encode in QR code
        size (int): Size of the QR code

    Returns:
        PIL.Image: QR code image
    """
    try:
        import qrcode

        qr = qrcode.QRCode(version=1, box_size=size // 25, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
    except ImportError:
        # Return a placeholder if qrcode is not available
        return Image.new("RGB", (size, size), color="white")


def create_label_pdf(label_info, output_path):
    """

    Create a PDF label from label information.


    Args:
        label_info (dict): Label information
        output_path (str): Path for the output PDF

    Returns:
        str: Path to the created PDF
    """
    # Create the label image first

    image_path = create_label_image(label_info)

    # Convert to PDF
    save_image_as_pdf(image_path, output_path)

    # Clean up temporary image
    if os.path.exists(image_path):
        os.remove(image_path)

    return output_path


def create_storage_label(storage_info):
    """

    Create a storage label for boxes or storage locations.


    Args:
        storage_info (dict): Storage information including location, contents, etc.

    Returns:
        str: Path to the created label image
    """
    # Use the box label creation function as a base

    return create_box_label_image(storage_info)
