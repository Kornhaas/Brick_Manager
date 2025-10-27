"""
This module handles the management of API tokens for external services like Rebrickable.

It provides functionality to generate, store, and manage user tokens securely
in the database configuration table.
"""

import logging
import requests
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from models import db, ConfigSettings
from cryptography.fernet import Fernet
import base64
import os

# pylint: disable=C0301,W0718

token_management_bp = Blueprint('token_management', __name__)

# Initialize logger
logger = logging.getLogger(__name__)

# Encryption key for securing tokens (in production, this should be in environment variables)
def get_encryption_key():
    """Get or create encryption key for token storage."""
    key_config = ConfigSettings.query.filter_by(key='encryption_key').first()
    if not key_config:
        # Generate new key
        key = Fernet.generate_key()
        key_config = ConfigSettings(
            key='encryption_key',
            value=base64.b64encode(key).decode(),
            encrypted=False,
            description='Encryption key for securing stored tokens'
        )
        db.session.add(key_config)
        db.session.commit()
        return key
    else:
        return base64.b64decode(key_config.value.encode())

def encrypt_token(token):
    """Encrypt a token for secure storage."""
    key = get_encryption_key()
    fernet = Fernet(key)
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    """Decrypt a stored token."""
    key = get_encryption_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_token.encode()).decode()

@token_management_bp.route('/token_management')
def token_management_page():
    """Display the token management page."""
    try:
        # Get current Rebrickable token status
        rebrickable_token = ConfigSettings.query.filter_by(key='rebrickable_user_token').first()
        token_exists = rebrickable_token is not None
        
        # Get Rebrickable username if stored
        rebrickable_username = ConfigSettings.query.filter_by(key='rebrickable_username').first()
        username = rebrickable_username.value if rebrickable_username else ''
        
        return render_template('token_management.html', 
                             token_exists=token_exists,
                             username=username)
    except Exception as e:
        logger.error(f"Error loading token management page: {e}")
        flash(f"Error loading token management page: {e}", 'error')
        return redirect(url_for('main.index'))

@token_management_bp.route('/generate_token', methods=['POST'])
def generate_token():
    """Generate a new Rebrickable user token."""
    try:
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'})
        
        # Rebrickable API endpoint for token generation
        url = 'https://rebrickable.com/api/v3/users/_token/'
        
        # Get the API key from config (this should be set separately)
        api_key_config = ConfigSettings.query.filter_by(key='rebrickable_api_key').first()
        if not api_key_config:
            return jsonify({'success': False, 
                          'message': 'Rebrickable API key not configured. Please contact administrator.'})
        
        api_key = api_key_config.value
        
        # Headers and data for the request
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        data = {
            'username': username,
            'password': password
        }
        
        # Make the request to Rebrickable
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code in [200, 201]:
            # Success - extract the token
            response_data = response.json()
            user_token = response_data.get('user_token')
            
            if user_token:
                # Encrypt and store the token
                encrypted_token = encrypt_token(user_token)
                
                # Update or create the token record
                rebrickable_token = ConfigSettings.query.filter_by(key='rebrickable_user_token').first()
                if rebrickable_token:
                    rebrickable_token.value = encrypted_token
                    rebrickable_token.updated_at = db.func.current_timestamp()
                else:
                    rebrickable_token = ConfigSettings(
                        key='rebrickable_user_token',
                        value=encrypted_token,
                        encrypted=True,
                        description='Encrypted Rebrickable user token for API access'
                    )
                    db.session.add(rebrickable_token)
                
                # Store the username for future reference
                rebrickable_username = ConfigSettings.query.filter_by(key='rebrickable_username').first()
                if rebrickable_username:
                    rebrickable_username.value = username
                    rebrickable_username.updated_at = db.func.current_timestamp()
                else:
                    rebrickable_username = ConfigSettings(
                        key='rebrickable_username',
                        value=username,
                        encrypted=False,
                        description='Rebrickable username for token generation'
                    )
                    db.session.add(rebrickable_username)
                
                db.session.commit()
                
                logger.info(f"Successfully generated and stored Rebrickable token for user: {username}")
                return jsonify({'success': True, 'message': 'Token generated and stored successfully!'})
            else:
                logger.error("No user_token in Rebrickable response")
                return jsonify({'success': False, 'message': 'Invalid response from Rebrickable API'})
        else:
            # Error from Rebrickable
            logger.error(f"Rebrickable API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 
                          'message': f'Rebrickable API error: {response.status_code} - {response.text}'})
            
    except requests.exceptions.Timeout:
        logger.error("Timeout connecting to Rebrickable API")
        return jsonify({'success': False, 'message': 'Timeout connecting to Rebrickable API'})
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error connecting to Rebrickable API: {e}")
        return jsonify({'success': False, 'message': f'Network error: {e}'})
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error generating token: {e}'})

@token_management_bp.route('/delete_token', methods=['POST'])
def delete_token():
    """Delete the stored Rebrickable user token."""
    try:
        # Delete the token
        rebrickable_token = ConfigSettings.query.filter_by(key='rebrickable_user_token').first()
        if rebrickable_token:
            db.session.delete(rebrickable_token)
            db.session.commit()
            logger.info("Rebrickable token deleted successfully")
            return jsonify({'success': True, 'message': 'Token deleted successfully!'})
        else:
            return jsonify({'success': False, 'message': 'No token found to delete'})
            
    except Exception as e:
        logger.error(f"Error deleting token: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting token: {e}'})

@token_management_bp.route('/test_token', methods=['POST'])
def test_token():
    """Test the stored Rebrickable user token."""
    try:
        # Get the stored token
        rebrickable_token = ConfigSettings.query.filter_by(key='rebrickable_user_token').first()
        if not rebrickable_token:
            return jsonify({'success': False, 'message': 'No token found to test'})
        
        # Decrypt the token
        user_token = decrypt_token(rebrickable_token.value)
        
        # Get the API key
        api_key_config = ConfigSettings.query.filter_by(key='rebrickable_api_key').first()
        if not api_key_config:
            return jsonify({'success': False, 
                          'message': 'Rebrickable API key not configured'})
        
        api_key = api_key_config.value
        
        # Test the token by making a simple API call
        test_url = f'https://rebrickable.com/api/v3/users/{user_token}/profile/'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        response = requests.get(test_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            profile_data = response.json()
            username = profile_data.get('username', 'Unknown')
            return jsonify({'success': True, 
                          'message': f'Token is valid! Connected as user: {username}'})
        else:
            logger.error(f"Token test failed: {response.status_code} - {response.text}")
            return jsonify({'success': False, 
                          'message': f'Token test failed: {response.status_code}'})
            
    except Exception as e:
        logger.error(f"Error testing token: {e}")
        return jsonify({'success': False, 'message': f'Error testing token: {e}'})