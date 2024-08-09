from flask import Blueprint, send_file, redirect, url_for, flash
from services.rebrickable_service import get_part_details, get_category_name
from services.label_service import create_label_image, save_image_as_pdf
from services.lookup_service import load_master_lookup
import os
from config import Config  # Import the Config class

label_bp = Blueprint('label', __name__)
master_lookup = load_master_lookup()

@label_bp.route('/create_label/<id>')
def create_label(id):
    part_details = get_part_details(id)

    if not part_details:
        flash(f"Failed to retrieve details for part {id}")
        return redirect(url_for('main.index'))

    name = part_details.get('name', 'Unknown Item')
    img_url = part_details.get('part_img_url', '')
    part_cat_id = part_details.get('part_cat_id', None)
    category = get_category_name(part_cat_id) if part_cat_id else 'Unknown Category'
    box = master_lookup.get(id, {}).get('box', 'Unknown Box')

    label_image_path = create_label_image(name, img_url, id, box, category)
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, f'label_{id}.pdf')
    save_image_as_pdf(label_image_path, pdf_path)

    return send_file(pdf_path, mimetype='application/pdf')
