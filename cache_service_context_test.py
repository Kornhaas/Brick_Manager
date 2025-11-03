#!/usr/bin/env python3
"""
Test cache service with proper Flask request context
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, '/app/brick_manager')

def test_cache_with_context():
    """Test cache service with proper Flask request context."""
    print("=== Cache Service Test with Request Context ===")
    
    try:
        from app import app
        from services.cache_service import cache_image
        
        # Configure Flask app for testing
        with app.app_context():
            # Set up minimal server configuration for url_for to work
            app.config['SERVER_NAME'] = 'localhost:5000'
            app.config['PREFERRED_URL_SCHEME'] = 'http'
            
            # Create a test request context
            with app.test_request_context('/'):
                print("✓ Request context established")
                
                # Test image URLs from your logs (already cached files)
                test_images = [
                    "https://cdn.rebrickable.com/media/parts/elements/6317714.jpg",
                    "https://cdn.rebrickable.com/media/parts/elements/6300350.jpg", 
                    "https://cdn.rebrickable.com/media/parts/elements/4632918.jpg"
                ]
                
                print(f"Testing cache service with {len(test_images)} images...")
                
                for i, url in enumerate(test_images, 1):
                    try:
                        print(f"\n[{i}/{len(test_images)}] Caching: {url}")
                        
                        # Use the cache service
                        result = cache_image(url)
                        print(f"✓ Cache result: {result}")
                        
                        # Extract filename to check if file exists
                        filename = os.path.basename(url)
                        cache_dir = app.config.get('CACHE_FOLDER')
                        if cache_dir:
                            images_dir = os.path.join(cache_dir, 'images')
                            file_path = os.path.join(images_dir, filename)
                            
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                print(f"✓ File exists: {file_path} ({file_size} bytes)")
                            else:
                                print(f"✗ File not found: {file_path}")
                        
                        app.logger.info(f"Cache service test successful: {url} -> {result}")
                        
                    except Exception as e:
                        print(f"✗ Failed to cache {url}: {e}")
                        app.logger.error(f"Cache service test failed for {url}: {e}")
                
                # Check final cache state
                print("\n=== Final Cache State ===")
                cache_dir = app.config.get('CACHE_FOLDER')
                if cache_dir:
                    images_dir = os.path.join(cache_dir, 'images')
                    if os.path.exists(images_dir):
                        cached_files = os.listdir(images_dir)
                        print(f"✓ Cached files: {len(cached_files)}")
                        
                        total_size = 0
                        for filename in cached_files:
                            filepath = os.path.join(images_dir, filename)
                            if os.path.isfile(filepath):
                                size = os.path.getsize(filepath)
                                total_size += size
                                print(f"  {filename}: {size} bytes")
                        
                        print(f"✓ Total cache size: {total_size} bytes")
                        app.logger.info(f"Cache service test completed: {len(cached_files)} files, {total_size} bytes total")
                        
                        print("✅ Cache service test PASSED - All functionality working!")
                    else:
                        print("✗ Cache directory not found")
                else:
                    print("✗ CACHE_FOLDER not configured")
                    
    except Exception as e:
        print(f"Cache service test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache_with_context()