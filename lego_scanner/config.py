import os

class Config:
    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    REBRICKABLE_TOKEN = os.getenv('REBRICKABLE_TOKEN')

    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

