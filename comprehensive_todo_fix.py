#!/usr/bin/env python3
"""
Comprehensive script to find and fix all malformed TODO docstrings in Python files.
This script identifies TODO docstrings that appear in function parameter lists and removes them.
"""

import os
import re
import ast

def fix_todo_docstrings_in_file(file_path):
    """Fix malformed TODO docstrings in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Pattern to match malformed TODO docstrings in parameter lists
        # These appear as standalone docstring lines in the middle of function definitions
        pattern = r'^\s*"""TODO:.*?"""$'
        
        lines = original_content.split('\n')
        fixed_lines = []
        removed_count = 0
        
        for line in lines:
            if re.match(pattern, line.strip()):
                print(f"  Removing: {line.strip()}")
                removed_count += 1
                continue  # Skip this line
            fixed_lines.append(line)
        
        if removed_count > 0:
            fixed_content = '\n'.join(fixed_lines)
            
            # Verify the fixed content has valid syntax
            try:
                ast.parse(fixed_content)
                
                # Write the fixed content back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                print(f"✅ Fixed {file_path}: Removed {removed_count} malformed TODO docstrings")
                return True
            except SyntaxError as e:
                print(f"❌ Syntax error after fixing {file_path}: {e}")
                return False
        else:
            print(f"✅ {file_path}: No malformed TODO docstrings found")
            return True
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def find_python_files(directory):
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to fix all TODO docstrings."""
    print("🔧 Starting comprehensive TODO docstring cleanup...")
    
    # Find all Python files in the brick_manager directory
    python_files = find_python_files('brick_manager')
    
    total_files = len(python_files)
    fixed_files = 0
    
    print(f"Found {total_files} Python files to check")
    
    for file_path in python_files:
        print(f"\n📁 Checking {file_path}...")
        if fix_todo_docstrings_in_file(file_path):
            fixed_files += 1
    
    print(f"\n🎉 Completed! Processed {fixed_files}/{total_files} files successfully")
    
    # Final verification - check syntax of all previously problematic files
    problematic_files = [
        'brick_manager/tests/test_app_comprehensive.py',
        'brick_manager/tests/test_coverage_boosters.py', 
        'brick_manager/tests/test_high_coverage_boost.py',
        'brick_manager/tests/test_large_modules_coverage.py',
        'brick_manager/tests/test_maximum_coverage.py',
        'brick_manager/tests/test_service_coverage.py',
        'brick_manager/services/rebrickable_sync_service.py'
    ]
    
    print("\n🔍 Final verification of previously problematic files:")
    all_good = True
    for file_path in problematic_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ {file_path}: Valid syntax")
        except SyntaxError as e:
            print(f"❌ {file_path}: Syntax error on line {e.lineno}: {e.text.strip() if e.text else ''}")
            all_good = False
        except FileNotFoundError:
            print(f"⚠️  {file_path}: File not found")
    
    if all_good:
        print("\n🎉 All files now have valid syntax!")
    else:
        print("\n❌ Some files still have syntax errors")

if __name__ == "__main__":
    main()