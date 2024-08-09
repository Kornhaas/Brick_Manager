from PIL import Image, ImageDraw, ImageFont
import os
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import requests

cm = 28.35  # 1 cm in points

def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))  # Temporary draw object

    while words:
        line = ''
        while words and draw.textbbox((0, 0), line + words[0], font=font)[2] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line)
    return lines

def create_label_image(name, img_url, item_id, box, category):
    width, height = int(12 * cm), int(8 * cm)
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
        font2 = ImageFont.truetype("arial.ttf", 24)
        font3 = ImageFont.truetype("arial.ttf", 26)
    except IOError:
        print("Font not found, using default font.")
        font = ImageFont.load_default()
        font2 = ImageFont.load_default()
        font3 = ImageFont.load_default()

    if img_url:
        try:
            item_image = Image.open(requests.get(img_url, stream=True).raw)
            item_image.thumbnail((width//2, height//2))
            image.paste(item_image, (width//4, height//4))
        except Exception as e:
            print(f"Failed to download or process image: {e}")

    max_width = width - 40
    lines = wrap_text(name, font2, max_width)

    y_text = 10
    for line in lines:
        draw.text((20, y_text), line, font=font2, fill="black")
        y_text += draw.textbbox((0, 0), line, font=font3)[3]

    draw.text((15, height - 60), f"Category: {category}", font=font, fill="black")
    draw.text((15, height - 40), f"ID: {item_id}", font=font2, fill="black")
    draw.text((width - 120, height - 40), f"Box: {box}", font=font3, fill="black")

    temp_image_path = os.path.join('uploads', f'label_{item_id}.png')
    image.save(temp_image_path, dpi=(300, 300))

    return temp_image_path

def save_image_as_pdf(image_path, pdf_path):
    img = Image.open(image_path)
    img_width, img_height = img.size

    c = canvas.Canvas(pdf_path, pagesize=(img_width, img_height))

    img_reader = ImageReader(image_path)
    c.drawImage(img_reader, 0, 0, width=img_width, height=img_height, preserveAspectRatio=True)

    c.save()
    print(f"Saved PDF as {pdf_path}")
