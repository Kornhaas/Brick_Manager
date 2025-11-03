#!/usr/bin/env python3
"""
Docker Activity Generator
Run this script in your Docker container to generate some logs and cache activity.
"""

import os
import sys
import time
from datetime import datetime

# Add the app directory to Python path  
sys.path.insert(0, '/app/brick_manager')

def generate_activity():
    """Generate some application activity to populate logs and cache."""
    print("=== Generating Docker Container Activity ===")
    
    try:
        from app import app
        from services.cache_service import cache_image
        
        with app.app_context():
            # Generate multiple log entries
            print("Generating log entries...")
            app.logger.info("=== Docker Activity Test Started ===")
            
            for i in range(5):
                app.logger.info(f"Activity test log entry {i+1}/5 at {datetime.now()}")
                app.logger.debug(f"Debug message {i+1}: Testing debug level logging")
                time.sleep(0.1)
            
            app.logger.warning("Test warning: This is a sample warning message")
            app.logger.error("Test error: This is a sample error message (can be ignored)")
            
            # Test multiple image caching
            print("Testing image caching with multiple URLs...")
            test_images = [
                "https://img.bricklink.com/ItemImage/PN/1/3001.png",
                "https://img.bricklink.com/ItemImage/PN/1/3003.png", 
                "https://img.bricklink.com/ItemImage/PN/1/3004.png"
            ]
            
            cached_count = 0
            for url in test_images:
                try:
                    app.logger.info(f"Attempting to cache image: {url}")
                    cached_path = cache_image(url)
                    if cached_path and os.path.exists(cached_path):
                        cached_count += 1
                        file_size = os.path.getsize(cached_path)
                        app.logger.info(f"Successfully cached image: {cached_path} ({file_size} bytes)")
                    else:
                        app.logger.warning(f"Image caching returned path but file not found: {cached_path}")
                except Exception as e:
                    app.logger.error(f"Failed to cache image {url}: {e}")
                
                time.sleep(0.5)
            
            app.logger.info(f"=== Activity Test Completed: {cached_count}/{len(test_images)} images cached ===")
            
            # Show final status
            print(f"\nActivity generation completed!")
            print(f"- Generated log entries in: {app.config.get('LOG_FOLDER')}")
            print(f"- Cached {cached_count} images in: {app.config.get('CACHE_FOLDER')}")
            
            # List final directory contents
            log_folder = app.config.get('LOG_FOLDER')
            if log_folder and os.path.exists(log_folder):
                log_files = os.listdir(log_folder)
                print(f"- Log directory contents: {log_files}")
            
            cache_folder = app.config.get('CACHE_FOLDER')
            if cache_folder:
                cache_images_dir = os.path.join(cache_folder, 'images')
                if os.path.exists(cache_images_dir):
                    cache_files = os.listdir(cache_images_dir)
                    print(f"- Cache images directory contents: {cache_files}")
                    
    except Exception as e:
        print(f"Activity generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_activity()