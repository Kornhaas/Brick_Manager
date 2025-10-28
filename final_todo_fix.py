#!/usr/bin/env python3
"""
Final comprehensive fix for all malformed TODO docstrings that appear 
within function parameter lists causing syntax errors.
"""

import re
import os

def fix_malformed_todos_in_file(file_path):
    """Fix malformed TODO docstrings within function parameter lists."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match TODO docstrings within function parameters
        # This matches lines that contain only whitespace and a TODO docstring
        pattern = r'^\s*"""TODO:.*?"""\s*$'
        
        # Remove TODO docstrings that appear on their own lines
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check if this line contains a standalone TODO docstring
            if re.match(pattern, line):
                # Skip this line (remove the TODO)
                print(f"  Removing line {i+1}: {line.strip()}")
                continue
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all files with malformed TODO docstrings."""
    files_to_fix = [
        'brick_manager/tests/test_app_comprehensive.py',
        'brick_manager/tests/test_coverage_boosters.py', 
        'brick_manager/tests/test_high_coverage_boost.py',
        'brick_manager/tests/test_large_modules_coverage.py',
        'brick_manager/tests/test_maximum_coverage.py',
        'brick_manager/tests/test_service_coverage.py'
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Processing {file_path}...")
            if fix_malformed_todos_in_file(file_path):
                print(f"✅ Fixed {file_path}")
                fixed_count += 1
            else:
                print(f"  No changes needed in {file_path}")
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")
    
    # Test all files for syntax errors
    print("\nTesting syntax...")
    import ast
    all_good = True
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
                print(f"✅ {file_path}")
            except SyntaxError as e:
                print(f"❌ {file_path}: line {e.lineno} - {e.msg}")
                all_good = False
    
    if all_good:
        print("\n🎉 All files now have valid syntax!")
    else:
        print("\n❌ Some files still have syntax errors.")

if __name__ == "__main__":
    main()