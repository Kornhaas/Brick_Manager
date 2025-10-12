"""
Token management service for retrieving and using stored API tokens.

This service provides utility functions for other parts of the application
to securely access stored tokens for API calls.
"""

import logging
from models import ConfigSettings
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

def get_encryption_key():
    """Get the encryption key from the database."""
    try:
        key_config = ConfigSettings.query.filter_by(key='encryption_key').first()
        if key_config:
            return base64.b64decode(key_config.value.encode())
        return None
    except Exception as e:
        logger.error(f"Error retrieving encryption key: {e}")
        return None

def decrypt_token(encrypted_token):
    """Decrypt a stored token."""
    try:
        key = get_encryption_key()
        if not key:
            return None
        fernet = Fernet(key)
        return fernet.decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        return None

def get_rebrickable_api_key():
    """Get the Rebrickable API key."""
    try:
        api_key_config = ConfigSettings.query.filter_by(key='rebrickable_api_key').first()
        return api_key_config.value if api_key_config else None
    except Exception as e:
        logger.error(f"Error retrieving API key: {e}")
        return None

def get_rebrickable_user_token():
    """Get the decrypted Rebrickable user token."""
    try:
        token_config = ConfigSettings.query.filter_by(key='rebrickable_user_token').first()
        if not token_config:
            return None
        return decrypt_token(token_config.value)
    except Exception as e:
        logger.error(f"Error retrieving user token: {e}")
        return None

def get_rebrickable_headers():
    """Get headers for Rebrickable API calls including both API key and user token."""
    try:
        api_key = get_rebrickable_api_key()
        user_token = get_rebrickable_user_token()
        
        if not api_key:
            logger.error("Rebrickable API key not configured")
            return None
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'key {api_key}'
        }
        
        if user_token:
            headers['User-Token'] = user_token
        
        return headers
    except Exception as e:
        logger.error(f"Error building Rebrickable headers: {e}")
        return None

def is_user_token_configured():
    """Check if a user token is configured."""
    try:
        token_config = ConfigSettings.query.filter_by(key='rebrickable_user_token').first()
        return token_config is not None
    except Exception as e:
        logger.error(f"Error checking token configuration: {e}")
        return False