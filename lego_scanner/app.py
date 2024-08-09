from flask import Flask
from routes.upload import upload_bp
from routes.label import label_bp
from routes.main import main_bp
from routes.storage import storage_bp

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set your secret key here

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(label_bp)
app.register_blueprint(main_bp)
app.register_blueprint(storage_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
