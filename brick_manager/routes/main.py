"""
This module defines the main route for the Brick Manager application.

It includes:
- A route to render the index (home) page.
- Health check endpoint for Docker monitoring.
"""


from flask import Blueprint, render_template, jsonify
from sqlalchemy import text
from models import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Render the index (home) page.

    Returns:
        Response: Renders the index.html template.
    """
    return render_template('index.html')


@main_bp.route('/health')
def health_check():
    """
    Health check endpoint for Docker monitoring.
    
    Returns:
        JSON response indicating application health status.
    """
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        return jsonify({
            'status': 'healthy',
            'message': 'Application is running properly',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'Health check failed: {str(e)}',
            'database': 'disconnected'
        }), 500
