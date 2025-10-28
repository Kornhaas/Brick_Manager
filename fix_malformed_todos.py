#!/usr/bin/env python3
"""
Fix malformed TODO docstrings that are inside function parameter lists.
This causes syntax errors as docstrings can't be in parameter definitions.
"""

import re
import os

def fix_malformed_function_definitions(file_path):
    """Fix functions with TODO docstrings inside parameter lists."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match function definitions with TODO docstrings in parameter lists
    # This matches: def function_name(\n    """TODO..."""\n    parameters...):
    pattern = r'(def\s+\w+\s*\(\s*)\n\s*"""TODO:.*?"""\s*\n(\s*[^)]*\s*\):)'
    
    # Replace by removing the TODO docstring
    content = re.sub(pattern, r'\1\n\2', content, flags=re.MULTILINE | re.DOTALL)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed malformed function definitions in {file_path}")
        return True
    return False

def main():
    # Files with known malformed function definitions
    files_to_fix = [
        'brick_manager/tests/test_app_comprehensive.py',
        'brick_manager/tests/test_coverage_boosters.py', 
        'brick_manager/tests/test_large_modules_coverage.py',
        'brick_manager/tests/test_maximum_coverage.py',
        'brick_manager/tests/test_service_coverage.py',
        'brick_manager/services/rebrickable_service.py',
        'brick_manager/services/rebrickable_sync_service.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fix_malformed_function_definitions(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()