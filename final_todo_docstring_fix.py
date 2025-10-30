#!/usr/bin/env python3
"""
Final comprehensive fix for all TODO docstring syntax errors.
This script removes malformed TODO docstrings and adds proper ones.
"""

import ast
import os
import re


def fix_todo_docstrings(file_path):
    """Fix malformed TODO docstrings in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for malformed TODO docstrings that cause syntax errors
            if ('"""TODO: Add docstring for' in line and 
                line.strip().startswith('"""') and 
                line.strip().endswith('."""')):
                
                # This is a malformed TODO docstring - skip it
                print(f"  Removing malformed TODO: {line.strip()}")
                i += 1
                continue
            
            # Check for function definitions without proper docstrings
            if line.strip().startswith('def ') and not line.strip().startswith('def _'):
                func_match = re.search(r'def\s+(\w+)\s*\(', line)
                if func_match:
                    func_name = func_match.group(1)
                    
                    # Look ahead to see if there's already a docstring
                    next_line_idx = i + 1
                    while (next_line_idx < len(lines) and 
                           lines[next_line_idx].strip() == ''):
                        next_line_idx += 1
                    
                    has_docstring = (next_line_idx < len(lines) and 
                                   '"""' in lines[next_line_idx] and
                                   not 'TODO:' in lines[next_line_idx])
                    
                    new_lines.append(line)
                    
                    if not has_docstring and not func_name.startswith('test_'):
                        # Add a proper docstring for non-test functions
                        indent = len(line) - len(line.lstrip()) + 4
                        docstring = f'{" " * indent}"""Function: {func_name}."""'
                        new_lines.append(docstring)
                    elif not has_docstring and func_name.startswith('test_'):
                        # Add a proper test docstring
                        indent = len(line) - len(line.lstrip()) + 4
                        test_description = func_name.replace('test_', '').replace('_', ' ').title()
                        docstring = f'{" " * indent}"""Test: {test_description}."""'
                        new_lines.append(docstring)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            
            i += 1
        
        new_content = '\n'.join(new_lines)
        
        # Verify the new content has valid syntax
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            print(f"  ❌ Syntax error after fix in {file_path}:{e.lineno}: {e.msg}")
            return False
        
        # Only write if content changed
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ Fixed {file_path}")
            return True
        else:
            print(f"  ⚪ No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix all Python files."""
    # Focus on the specific files mentioned in the error
    error_files = [
        'brick_manager/tests/test_app_comprehensive.py',
        'brick_manager/tests/test_coverage_boosters.py', 
        'brick_manager/tests/test_high_coverage_boost.py',
        'brick_manager/tests/test_large_modules_coverage.py',
        'brick_manager/tests/test_maximum_coverage.py',
        'brick_manager/tests/test_service_coverage.py'
    ]
    
    print("🔧 Fixing specific test files with TODO docstring errors...")
    
    for file_path in error_files:
        if os.path.exists(file_path):
            fix_todo_docstrings(file_path)
        else:
            print(f"  ⚠️ File not found: {file_path}")
    
    # Also fix any other files in the tests directory
    print("\n🔧 Checking all other test files...")
    
    test_dir = 'brick_manager/tests'
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            if file.endswith('.py') and file not in [os.path.basename(f) for f in error_files]:
                file_path = os.path.join(test_dir, file)
                fix_todo_docstrings(file_path)
    
    print("\n🎉 TODO docstring fix completed!")


if __name__ == "__main__":
    main()