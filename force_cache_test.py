#!/usr/bin/env python3
"""
Force image caching test for Docker container
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, '/app/brick_manager')

def force_cache_images():
    """Force download and cache some images to test the cache system."""
    print("=== Force Caching Test ===")
    
    try:
        from app import app
        from services.cache_service import cache_image
        
        with app.app_context():
            # Test images from your actual logs
            test_images = [
                "https://cdn.rebrickable.com/media/parts/elements/6317714.jpg",
                "https://cdn.rebrickable.com/media/parts/elements/6300350.jpg", 
                "https://cdn.rebrickable.com/media/parts/elements/4632918.jpg"
            ]
            
            print(f"Attempting to cache {len(test_images)} images...")
            
            for i, url in enumerate(test_images, 1):
                try:
                    print(f"\n[{i}/{len(test_images)}] Caching: {url}")
                    
                    # Force cache the image
                    cached_path = cache_image(url)
                    print(f"✓ Cached to: {cached_path}")
                    
                    # Check if file was actually created
                    if cached_path and os.path.exists(cached_path):
                        file_size = os.path.getsize(cached_path)
                        print(f"✓ File size: {file_size} bytes")
                        app.logger.info(f"Successfully cached image: {url} -> {cached_path} ({file_size} bytes)")
                    else:
                        print(f"✗ File not found at: {cached_path}")
                        app.logger.warning(f"Cache returned path but file not found: {cached_path}")
                        
                except Exception as e:
                    print(f"✗ Failed to cache {url}: {e}")
                    app.logger.error(f"Failed to cache image {url}: {e}")
            
            # Check final cache state
            print("\n=== Final Cache State ===")
            cache_dir = "/app/data/cache/images"
            if os.path.exists(cache_dir):
                cached_files = os.listdir(cache_dir)
                print(f"✓ Cached files: {len(cached_files)}")
                
                total_size = 0
                for filename in cached_files:
                    filepath = os.path.join(cache_dir, filename)
                    if os.path.isfile(filepath):
                        size = os.path.getsize(filepath)
                        total_size += size
                        print(f"  {filename}: {size} bytes")
                
                print(f"✓ Total cache size: {total_size} bytes")
                app.logger.info(f"Cache test completed: {len(cached_files)} files, {total_size} bytes total")
            else:
                print("✗ Cache directory not found")
                
    except Exception as e:
        print(f"Cache test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    force_cache_images()