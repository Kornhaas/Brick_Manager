"""
This module defines the main route for the Brick Manager application.

It includes:
- A route to render the index (home) page.
"""


from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Render the index (home) page.

    Returns:
        Response: Renders the index.html template.
    """
    return render_template('index.html')
