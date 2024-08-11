"""
This module handles the file upload functionality for the LEGO Scanner application.

It includes:
- Uploading and saving files to the server.
- Checking the validity of the uploaded files.
- Fetching predictions based on the uploaded image.
- Augmenting prediction results with additional information from the master lookup.
"""

import os  # Standard library import
# Third-party imports
from flask import Blueprint, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
from services.lookup_service import load_master_lookup  # Local imports
from services.rebrickable_service import get_predictions
from config import Config

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/upload', methods=['POST'])
def upload():
    """
    Handle file upload, validate the file, and process predictions.

    Returns:
        Response: Renders the results template if successful, otherwise redirects to the main index.
    """
    master_lookup = load_master_lookup()

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

        flash("Invalid result structure or no items found")
        return redirect(url_for('main.index'))

    flash('Allowed file types are png, jpg, jpeg, gif')
    return redirect(url_for('main.index'))


def allowed_file(filename):
    """
    Check if the uploaded file is of an allowed type.

    Args:
        filename (str): The name of the uploaded file.

    Returns:
        bool: True if the file is of an allowed type, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
