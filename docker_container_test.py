#!/usr/bin/env python3
"""
Docker Container Test Script
Run this inside your Docker container to test logging and cache functionality.
"""

import os
import sys
import requests
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, '/app/brick_manager')

def test_inside_docker():
    """Test functionality inside Docker container."""
    print("=== Docker Container Functionality Test ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    try:
        # Import Flask app
        from app import app
        from services.cache_service import get_cache_directory, cache_image
        
        with app.app_context():
            print("\n--- Configuration Check ---")
            print(f"CACHE_FOLDER: {app.config.get('CACHE_FOLDER')}")
            print(f"LOG_FOLDER: {app.config.get('LOG_FOLDER')}")
            print(f"Docker environment: {os.path.exists('/app/data')}")
            
            # Test logging
            print("\n--- Testing Logging ---")
            app.logger.info(f"Docker test log entry at {datetime.now()}")
            app.logger.warning("This is a test warning message")
            app.logger.error("This is a test error message (ignore this)")
            
            log_folder = app.config.get('LOG_FOLDER')
            log_file = os.path.join(log_folder, 'brick_manager.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    print(f"Log file exists with {len(lines)} lines")
                    if lines:
                        print("Last few log entries:")
                        for line in lines[-3:]:
                            print(f"  {line.strip()}")
            else:
                print(f"Log file not found at: {log_file}")
            
            # Test cache directory
            print("\n--- Testing Cache Directory ---")
            cache_dir = get_cache_directory()
            print(f"Cache directory: {cache_dir}")
            print(f"Cache directory exists: {os.path.exists(cache_dir)}")
            
            # Test cache functionality with a real image
            print("\n--- Testing Image Caching ---")
            test_image_url = "https://img.bricklink.com/ItemImage/PN/1/3001.png"
            try:
                cached_image_path = cache_image(test_image_url)
                print(f"Image cached successfully: {cached_image_path}")
                
                # Check if file was actually created
                if os.path.exists(cached_image_path):
                    file_size = os.path.getsize(cached_image_path)
                    print(f"Cached file size: {file_size} bytes")
                else:
                    print("Cached image file not found")
                    
            except Exception as e:
                print(f"Image caching test failed: {e}")
            
            # List cache directory contents
            try:
                cache_contents = os.listdir(cache_dir)
                print(f"Cache directory contents: {cache_contents}")
            except Exception as e:
                print(f"Could not list cache directory: {e}")
            
            print("\n--- Directory Structure Check ---")
            data_dirs = ['/app/data', '/app/data/cache', '/app/data/logs', '/app/data/cache/images']
            for dir_path in data_dirs:
                if os.path.exists(dir_path):
                    try:
                        contents = os.listdir(dir_path)
                        print(f"{dir_path}: {contents}")
                    except Exception as e:
                        print(f"{dir_path}: Error listing - {e}")
                else:
                    print(f"{dir_path}: Does not exist")
                    
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inside_docker()