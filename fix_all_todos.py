#!/usr/bin/env python3
"""Remove all problematic TODO docstrings that cause syntax errors."""

import os
import re

# List of files to fix
files_to_fix = [
    'brick_manager/app.py',
    'brick_manager/models.py', 
    'brick_manager/routes/import_rebrickable_data.py',
    'brick_manager/routes/set_maintain.py',
    'brick_manager/tests/test_app_comprehensive.py',
    'brick_manager/tests/test_coverage_boosters.py',
    'brick_manager/tests/test_high_coverage_boost.py',
    'brick_manager/tests/test_integration.py',
    'brick_manager/tests/test_large_modules_coverage.py',
    'brick_manager/tests/test_main_routes.py',
    'brick_manager/tests/test_maximum_coverage.py',
    'brick_manager/tests/test_part_lookup_service.py',
    'brick_manager/tests/test_service_coverage.py'
]

def fix_file(file_path):
    """Remove problematic TODO docstrings that cause syntax errors."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Track lines to remove
    lines_to_remove = []
    
    for i, line in enumerate(lines):
        # Check if this line contains a TODO docstring that causes syntax errors
        # These are typically standalone docstring lines in function parameter lists
        if '"""TODO: Add docstring for' in line and line.strip().startswith('"""'):
            # Check if this is within a function definition (look at previous lines)
            for j in range(max(0, i-5), i):
                if 'def ' in lines[j] and '(' in lines[j] and ')' not in lines[j]:
                    # This is likely a problematic TODO within function parameters
                    lines_to_remove.append(i)
                    break
    
    # Remove the problematic lines
    if lines_to_remove:
        for line_idx in reversed(lines_to_remove):  # Remove from end to preserve indices
            del lines[line_idx]
        
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"Fixed {file_path} - removed {len(lines_to_remove)} problematic TODO lines")
    else:
        print(f"No issues found in {file_path}")

# Fix all the files
for file_path in files_to_fix:
    fix_file(file_path)

print("All files processed")