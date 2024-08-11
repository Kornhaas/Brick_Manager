from flask import Blueprint, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
import os
from services.lookup_service import load_master_lookup
from services.rebrickable_service import get_predictions
from config import Config

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload():
    master_lookup = load_master_lookup()  # This should correctly call the function

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('main.index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)

        result = get_predictions(file_path, filename)

        if result:
            for item in result.get('items', []):
                item_id = item.get('id')
                if item_id in master_lookup:
                    item['lookup_info'] = master_lookup[item_id]
            return render_template('results.html', result=result)
        else:
            flash("Invalid result structure or no items found")
            return redirect(url_for('main.index'))
    else:
        flash('Allowed file types are png, jpg, jpeg, gif')
        return redirect(url_for('main.index'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
