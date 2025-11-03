#!/usr/bin/env python3
"""
Test script to validate Docker container path configuration.
This script tests that logs and cache directories are properly configured and writable.
"""

import os
import sys
sys.path.insert(0, '/workspaces/Brick_Manager/brick_manager')

from brick_manager.app import app
from brick_manager.services.cache_service import get_cache_directory
import tempfile
import logging

def test_docker_configuration():
    """Test that Docker environment is properly configured."""
    print("=== Docker Configuration Test ===")
    
    with app.app_context():
        # Test configuration values
        print(f"CACHE_FOLDER: {app.config.get('CACHE_FOLDER')}")
        print(f"LOG_FOLDER: {app.config.get('LOG_FOLDER')}")
        print(f"UPLOAD_FOLDER: {app.config.get('UPLOAD_FOLDER')}")
        print(f"OUTPUT_FOLDER: {app.config.get('OUTPUT_FOLDER')}")
        print(f"INSTANCE_FOLDER: {app.config.get('INSTANCE_FOLDER')}")
        
        # Test if we're in Docker environment
        is_docker = os.path.exists("/app/data")
        print(f"Docker environment detected: {is_docker}")
        
        # Test cache directory
        cache_dir = get_cache_directory()
        print(f"Cache images directory: {cache_dir}")
        print(f"Cache directory exists: {os.path.exists(cache_dir)}")
        
        # Test log directory
        log_folder = app.config.get('LOG_FOLDER')
        if log_folder:
            print(f"Log directory exists: {os.path.exists(log_folder)}")
            
            # Test write access to log directory
            try:
                test_log_file = os.path.join(log_folder, "test_write.log")
                with open(test_log_file, 'w') as f:
                    f.write("Test log entry")
                os.remove(test_log_file)
                print("Log directory is writable: True")
            except Exception as e:
                print(f"Log directory is writable: False - {e}")
        
        # Test cache directory write access
        try:
            test_cache_file = os.path.join(cache_dir, "test_cache.txt")
            with open(test_cache_file, 'w') as f:
                f.write("Test cache entry")
            os.remove(test_cache_file)
            print("Cache directory is writable: True")
        except Exception as e:
            print(f"Cache directory is writable: False - {e}")
        
        # Test application logging
        try:
            app.logger.info("Test log message from Docker configuration test")
            print("Application logging test: Success")
        except Exception as e:
            print(f"Application logging test: Failed - {e}")

if __name__ == "__main__":
    test_docker_configuration()