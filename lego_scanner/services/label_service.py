"""
This module provides functions to create label images and save them as PDFs
for the LEGO Scanner application.

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

CM = 28.35  # 1 cm in points


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
    except IOError:
        print("Font not found, using default font.")
        font = ImageFont.load_default()
        font2 = ImageFont.load_default()
        font3 = ImageFont.load_default()
    return font, font2, font3


def download_image(img_url):
    """
    Download an image from a URL.

    Args:
        img_url (str): The URL of the image to download.

    Returns:
        Image: The downloaded image, or None if the download fails.
    """
    if img_url:
        try:
            response = requests.get(img_url, stream=True, timeout=10)
            response.raise_for_status()
            return Image.open(response.raw)
        except requests.RequestException as e:
            print(f"Failed to download or process image: {e}")
            return None
    return None


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

    lines = wrap_text(text_info['text'], font, max_width)
    for line in lines:
        draw.text((x, y + y_offset), line, font=font, fill="black")
        y_offset += draw.textbbox((0, 0), line, font=font)[3]
    return y_offset


def create_label_image(label_info):
    """
    Create a label image with part details.

    Args:
        label_info (dict): A dictionary containing label details 
        such as name, item_id, box, category, and img_url.

    Returns:
        str: The path to the saved label image.
    """
    logging.info(f"Creating label for item {label_info['item_id']}")
    logging.debug(f"Label info: {label_info}")

    width, height = int(12 * CM), int(8 * CM)
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    font, font2, font3 = load_fonts()

    # Load the image
    item_image = None
    img_url = label_info['img_url']
    if img_url.startswith('/static/'):
        # Handle local cached image path
        local_path = img_url.lstrip('/')
        if os.path.exists(local_path):
            item_image = Image.open(local_path)
        else:
            logging.warning(f"Cached image not found at {local_path}")
    else:
        # Try downloading the image if it's a URL
        item_image = download_image(img_url)

    if item_image:
        item_image.thumbnail((width // 2, height // 2))
        image.paste(item_image, (width // 4, height // 4))
    else:
        logging.warning("No image available for this part")

    # Draw text on the label
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
              f"{label_info['category']}", font=font, fill="blue")

    # Save the label as an image
    temp_image_path = os.path.join(
        'uploads', f'label_{label_info["item_id"]}.png')
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
    c.drawImage(img_reader, 0, 0, width=img_width,
                height=img_height, preserveAspectRatio=True)

    c.save()
    print(f"Saved PDF as {pdf_path}")
