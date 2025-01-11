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
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import requests
from services.cache_service import cache_image  # Import the cache_image function
#pylint: disable=W0718,R0914
CM = 28.35  # 1 cm in points


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
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # Temporary draw object

    while words:
        line = ''
        while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line)
    return lines


def load_fonts():
    """
    Load fonts for the label.

    Returns:
        tuple: A tuple containing three different font sizes.
    """
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font2 = ImageFont.truetype("arial.ttf", 24)
        font3 = ImageFont.truetype("arial.ttf", 26)
        font4 = ImageFont.truetype("arial.ttf", 10)
    except IOError:
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
    x, y = text_info['position']
    font = text_info['font']
    max_width = text_info['max_width']
    y_offset = text_info.get('y_offset', 0)

    logging.debug(
        "Drawing text: %s at position (%d, %d) with max_width %d",
        text_info['text'], x, y, max_width
    )

    try:
        lines = wrap_text(text_info['text'], font, max_width)
        logging.debug("Wrapped text into %d lines: %s", len(lines), lines)

        for line in lines:
            draw.text((x, y + y_offset), line, font=font, fill="black")
            y_offset += draw.textbbox((0, 0), line, font=font)[3]
            logging.debug("Rendered line: %s, y_offset now: %d",
                          line, y_offset)

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
    x, y = text_info['position']
    max_width = text_info['max_width']
    y_offset = text_info.get('y_offset', 0)
    text = text_info['text']

    logging.debug(
        "Drawing text: %s at position (%d, %d) with max_width %d",
        text, x, y, max_width
    )

    base_font_path = "arial.ttf"
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
            logging.error("Error loading font at size %d: %s",
                          font_size, error)
            font = ImageFont.load_default()
        font_size -= 1

    logging.debug("Using font size %d for text: %s", font_size, text)

    lines = wrap_text(text, font, max_width)
    logging.debug("Wrapped text into %d lines: %s", len(lines), lines)

    for line in lines:
        bbox = draw.textbbox((x, y + y_offset), line, font=font)
        draw.text((x, y + y_offset), line, font=font, fill="black")
        y_offset += bbox[3] - bbox[1]
        logging.debug("Rendered line: %s, updated y_offset: %d",
                      line, y_offset)

    return y_offset


def create_label_image(label_info):
    """
    Create a label image with part details.

    Args:
        label_info (dict): A dictionary containing label details.

    Returns:
        str: The path to the saved label image.
    """
    logging.info("Creating label for item %s", label_info['item_id'])
    width, height = int(12 * CM), int(8 * CM)
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    font, font2, font3, _ = load_fonts()
    cached_image_url = cache_image(label_info['img_url'])
    item_image = download_image(cached_image_url)

    if item_image:
        item_image.thumbnail((width // 2, height // 2))
        image.paste(item_image, (width // 4, height // 4))
    else:
        logging.warning("No image available for this part")

    draw_text(draw, {
        'text': label_info['name'],
        'position': (20, 10),
        'font': font2,
        'max_width': width - 40
    })

    draw.text((15, height - 60),
              f"{label_info['item_id']}", font=font2, fill="black")
    draw.text((width - 120, height - 60),
              f"Box: {label_info['box']}", font=font3, fill="black")
    draw.text((50, height - 30),
              label_info['category'], font=font, fill="blue")

    temp_image_path = os.path.join(
        'uploads', f"label_{label_info['item_id']}.png")
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
        box_info.get('box', 'unknown'),
        box_info.get('location', 'unknown'),
        box_info.get('level', 'unknown'),
    )
    logging.debug("Box info: %s", box_info)

    # Correct label size: 14cm x 7cm
    width, height = int(14 * CM), int(6.5 * CM)
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    font, _, font3, _ = load_fonts()
    items = box_info.get('items', [])
    num_items = len(items)
    logging.debug("Number of items to process: %d", num_items)

    # Handle case with no items
    if num_items == 0:
        logging.warning(
            "No items found in the box %s. Skipping label generation.", box_info.get('box'))
        draw.text((width // 2, height // 2), "No items available",
                  font=font, fill="red", anchor="mm")
        temp_image_path = os.path.join(
            'uploads',
            f'{box_info.get("location", "unknown")}_{box_info.get("level", "unknown")}_{
                box_info.get("box", "unknown")}_label.jpg'
        )
        image.save(temp_image_path, dpi=(300, 300))
        return temp_image_path

    # Adjusted maximum dimensions for images
    max_image_width = int(width / num_items)
    max_image_height = int(height * 0.4)

    # Spacing for text
    text_y_offset = int(height * 0.45)

    for idx, item in enumerate(items):
        logging.debug("Processing item %d/%d: %s", idx +
                      1, num_items, item.get('part_num'))

        # Use cache_image to get the image URL
        cached_image_url = cache_image(item.get('img_url'))
        item_image = download_image(cached_image_url)

        # Calculate x position for this item
        x_start = idx * (width // num_items)
        x_center = x_start + (max_image_width // 2)

        if item_image:
            logging.debug("Original image size for %s: %s",
                          item.get('part_num'), item_image.size)
            item_image.thumbnail((max_image_width, max_image_height))
            logging.debug("Resized image size for %s: %s",
                          item.get('part_num'), item_image.size)

            # Center the image in its slot
            x_image_offset = x_center - (item_image.width // 2)
            image.paste(item_image, (x_image_offset, 5))
        else:
            logging.warning("No image available for part %s",
                            item.get('part_num'))

        # Calculate the text width and center the text
        draw_text_dynamic(draw, {
            'text': item.get('part_num', 'Unknown'),
            'position': (x_center - (max_image_width // 2), text_y_offset),
            'max_width': max_image_width
        })

    # Add the category of the first item at the bottom
    if items:
        first_item_category = items[0].get('category', 'No Category')
        category_text_width = draw.textbbox(
            (0, 0), first_item_category, font=font3)[2]
        x_category_offset = (width // 2) - (category_text_width // 2)
        draw.text(
            (x_category_offset, height - 50),  # Position near the bottom
            first_item_category,
            font=font3,
            fill="blue"
        )

    # Add the box number in bold in the bottom-right corner
    box_number_text = f"{box_info.get('box', 'unknown')}"
    box_number_width = draw.textbbox((0, 0), box_number_text, font=font3)[2]
    box_x = width - box_number_width - 10  # Bottom-right corner with padding
    box_y = height - 30

    # Simulate bold text by drawing the same text multiple times with slight offsets
    for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        draw.text((box_x + offset[0], box_y + offset[1]),
                  box_number_text, font=font3, fill="red")

    # Construct the filename dynamically
    location = box_info.get('location', 'unknown').replace(' ', '_')
    level = box_info.get('level', 'unknown').replace(' ', '_')
    box = box_info.get('box', 'unknown').replace(' ', '_')
    filename = f"{location}_{level}_{box}_label.png"

    # Define the full path for saving the image
    temp_image_path = os.path.join('uploads', filename)

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
    logging.info("Generating JPG label for box %s.",
                 box_info.get('box', 'unknown'))
    image_path = create_box_label_image(box_info)  # Create the label image

    # Convert the PNG image to a JPG image
    jpg_path = os.path.splitext(image_path)[0] + '.jpg'
    with Image.open(image_path) as img:
        rgb_image = img.convert("RGB")  # Ensure RGB format for JPG
        # Save as JPG with high quality
        rgb_image.save(jpg_path, "JPEG", quality=95)

    logging.info("Box label saved as JPG: %s", jpg_path)
    os.remove(image_path)  # Remove the temporary PNG file

    return jpg_path
