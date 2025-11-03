#!/usr/bin/env python3
"""
Simple Docker log file checker
"""

import os
import sys

def check_log_files():
    """Check if log files exist in the mounted directories."""
    print("=== Checking Docker Log Files ===")
    
    # Check log directory
    log_dir = "/app/data/logs"
    print(f"Checking log directory: {log_dir}")
    
    if os.path.exists(log_dir):
        print(f"✓ Log directory exists")
        try:
            files = os.listdir(log_dir)
            print(f"✓ Log directory contents: {files}")
            
            # Check for the main log file
            log_file = os.path.join(log_dir, "brick_manager.log")
            if os.path.exists(log_file):
                print(f"✓ Log file exists: {log_file}")
                file_size = os.path.getsize(log_file)
                print(f"✓ Log file size: {file_size} bytes")
                
                # Show last few lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    print(f"✓ Total log lines: {len(lines)}")
                    if lines:
                        print("Last 3 log entries:")
                        for line in lines[-3:]:
                            print(f"  {line.strip()}")
            else:
                print(f"✗ Log file not found: {log_file}")
        except Exception as e:
            print(f"✗ Error reading log directory: {e}")
    else:
        print(f"✗ Log directory does not exist: {log_dir}")
    
    # Check cache directory
    cache_dir = "/app/data/cache"
    print(f"\nChecking cache directory: {cache_dir}")
    
    if os.path.exists(cache_dir):
        print(f"✓ Cache directory exists")
        try:
            files = os.listdir(cache_dir)
            print(f"✓ Cache directory contents: {files}")
            
            # Check images subdirectory
            images_dir = os.path.join(cache_dir, "images")
            if os.path.exists(images_dir):
                print(f"✓ Images directory exists: {images_dir}")
                image_files = os.listdir(images_dir)
                print(f"✓ Cached images: {image_files}")
                
                # Show file sizes
                for img_file in image_files:
                    img_path = os.path.join(images_dir, img_file)
                    if os.path.isfile(img_path):
                        size = os.path.getsize(img_path)
                        print(f"  {img_file}: {size} bytes")
            else:
                print(f"✗ Images directory not found: {images_dir}")
        except Exception as e:
            print(f"✗ Error reading cache directory: {e}")
    else:
        print(f"✗ Cache directory does not exist: {cache_dir}")

if __name__ == "__main__":
    check_log_files()