#!/usr/bin/env python3
"""
Simple image download test for Docker container
"""

import os
import sys
import requests

# Add the app directory to Python path
sys.path.insert(0, '/app/brick_manager')

def test_simple_download():
    """Test simple image downloading without Flask complications."""
    print("=== Simple Image Download Test ===")
    
    try:
        from app import app
        
        with app.app_context():
            # Get cache directory
            cache_dir = app.config.get('CACHE_FOLDER')
            if cache_dir:
                images_dir = os.path.join(cache_dir, 'images')
                os.makedirs(images_dir, exist_ok=True)
                print(f"✓ Cache directory: {images_dir}")
            else:
                print("✗ CACHE_FOLDER not configured")
                return
            
            # Test image URLs from your logs
            test_images = [
                "https://cdn.rebrickable.com/media/parts/elements/6317714.jpg",
                "https://cdn.rebrickable.com/media/parts/elements/6300350.jpg", 
                "https://cdn.rebrickable.com/media/parts/elements/4632918.jpg"
            ]
            
            print(f"Downloading {len(test_images)} images...")
            
            for i, url in enumerate(test_images, 1):
                try:
                    print(f"\n[{i}/{len(test_images)}] Downloading: {url}")
                    
                    # Extract filename from URL
                    filename = os.path.basename(url)
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    
                    file_path = os.path.join(images_dir, filename)
                    
                    # Download the image
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    # Save to cache
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = os.path.getsize(file_path)
                    print(f"✓ Downloaded: {filename} ({file_size} bytes)")
                    app.logger.info(f"Downloaded image: {url} -> {file_path} ({file_size} bytes)")
                    
                except Exception as e:
                    print(f"✗ Failed to download {url}: {e}")
                    app.logger.error(f"Failed to download image {url}: {e}")
            
            # Check final state
            print("\n=== Final Cache State ===")
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
                app.logger.info(f"Download test completed: {len(cached_files)} files, {total_size} bytes total")
            else:
                print("✗ Cache directory not found")
                
    except Exception as e:
        print(f"Download test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_download()