#!/usr/bin/env python3
"""
Script to set up initial configuration for the Rebrickable API key.
This should be run once to initialize the API key in the database.
"""

import sys
import os

# Add the current directory to the path so we can import models
sys.path.insert(0, '.')

try:
    from app import app, db
    from models import ConfigSettings
    
    # The Rebrickable API key (should be configured by administrator)
    REBRICKABLE_API_KEY = "b2c9a7eed2146bafdfe49f8d17b1faea"  # From your API example
    
    with app.app_context():
        print("Setting up Rebrickable API configuration...")
        
        # Check if API key already exists
        api_key_config = ConfigSettings.query.filter_by(key='rebrickable_api_key').first()
        
        if api_key_config:
            print("API key already configured")
            print(f"Current API key: {api_key_config.value[:10]}...")
            update = input("Do you want to update it? (y/N): ").lower().strip()
            if update == 'y':
                api_key_config.value = REBRICKABLE_API_KEY
                api_key_config.updated_at = db.func.current_timestamp()
                db.session.commit()
                print("API key updated successfully!")
            else:
                print("API key unchanged")
        else:
            # Create new API key configuration
            api_key_config = ConfigSettings(
                key='rebrickable_api_key',
                value=REBRICKABLE_API_KEY,
                encrypted=False,
                description='Rebrickable API key for accessing the API'
            )
            db.session.add(api_key_config)
            db.session.commit()
            print("API key configured successfully!")
        
        print("\nConfiguration completed. You can now use the Token Management page to generate user tokens.")
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the brick_manager directory")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()