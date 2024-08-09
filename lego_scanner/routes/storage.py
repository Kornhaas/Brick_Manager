# routes/storage.py
from flask import Blueprint, render_template, request, redirect, url_for

storage_bp = Blueprint('storage', __name__)

@storage_bp.route('/add_to_storage/<id>', methods=['GET', 'POST'])
def add_to_storage(id):
    if request.method == 'POST':
        location = request.form.get('location')
        level = request.form.get('level')
        box = request.form.get('box')
        
        # Logic to save storage info
        print(f"Stored item {id} at Location: {location}, Level: {level}, Box: {box}")
        return redirect(url_for('main.index'))
    
    return render_template('storage.html', item_id=id)
