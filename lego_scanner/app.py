from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import os
import requests
from werkzeug.utils import secure_filename
from .lookup import load_master_lookup  # Import the function

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Load the master lookup table
master_lookup = load_master_lookup('master_lookup.json')

# Configure upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Handle file upload and API request
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Send image to external API
        api_url = "https://api.brickognize.com/predict/"
        headers = {
            'accept': 'application/json',
        }
        files = {
            'query_image': (filename, open(file_path, 'rb'), 'image/jpeg')
        }
        
        response = requests.post(api_url, headers=headers, files=files)
        
        try:
            result = response.json()
            #print("API Response:", result)  # Debug print statement
        except ValueError:
            flash("Error decoding JSON response from the API")
            return redirect(url_for('index'))

        # Check if 'items' is in the result and is a list
        if 'items' in result and isinstance(result['items'], list):
            # Use the master lookup table to add additional information
            for item in result['items']:
                print(item)
                item_id = item.get('id')
                print(f"Checking item {item_id} in the lookup table")
                if item_id in master_lookup:
                    print(f"Found item {item_id} in the lookup table")
                    item['lookup_info'] = master_lookup[item_id]
                    print(f"Added lookup info for item {item_id}")
                    print(item['lookup_info'])
            return render_template('results.html', result=result)
        else:
            flash("Invalid result structure or no items found")
            print("Invalid result structure:", result)
            return redirect(url_for('index'))
    else:
        flash('Allowed file types are png, jpg, jpeg, gif')
        return redirect(url_for('index'))

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Add to storage route
@app.route('/add_to_storage', methods=['POST'])
def add_to_storage():
    # Implement storing logic here
    location = request.form.get('location')
    level = request.form.get('level')
    box = request.form.get('box')
    
    # Save storage info to a file (or database)
    # For simplicity, let's just print it
    print(f"Stored at Location: {location}, Level: {level}, Box: {box}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
