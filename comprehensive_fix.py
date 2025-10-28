#!/usr/bin/env python3
"""
Comprehensive fix for all malformed TODO docstrings in function parameter lists.
"""

import os
import subprocess

def find_and_fix_syntax_errors():
    """Find all Python files with syntax errors and fix them."""
    
    # First, find all Python files
    result = subprocess.run(['find', '.', '-name', '*.py'], capture_output=True, text=True)
    python_files = result.stdout.strip().split('\n')
    
    fixed_files = []
    
    for file_path in python_files:
        if not file_path or not file_path.endswith('.py'):
            continue
            
        # Check if file has syntax errors
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Try to parse
            import ast
            ast.parse(content)
            
        except SyntaxError as e:
            if 'TODO' in str(e.text) and 'docstring' in str(e.text):
                print(f"Fixing TODO syntax error in {file_path} at line {e.lineno}")
                
                # Read all lines
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Remove the problematic line
                if e.lineno <= len(lines):
                    line_content = lines[e.lineno - 1].strip()
                    if 'TODO' in line_content and 'docstring' in line_content:
                        lines.pop(e.lineno - 1)
                        
                        # Write back
                        with open(file_path, 'w') as f:
                            f.writelines(lines)
                        
                        fixed_files.append(file_path)
                        print(f"  Removed line {e.lineno}: {line_content}")
        except Exception:
            # Skip files that can't be read or parsed for other reasons
            continue
    
    return fixed_files

def main():
    print("Finding and fixing TODO syntax errors...")
    fixed_files = find_and_fix_syntax_errors()
    
    if fixed_files:
        print(f"\nFixed {len(fixed_files)} files:")
        for file_path in fixed_files:
            print(f"  - {file_path}")
    else:
        print("\nNo files needed fixing.")
    
    # Test all the problematic files again
    print("\nTesting previously problematic files...")
    test_files = [
        './brick_manager/tests/test_app_comprehensive.py',
        './brick_manager/tests/test_coverage_boosters.py', 
        './brick_manager/tests/test_large_modules_coverage.py',
        './brick_manager/tests/test_maximum_coverage.py',
        './brick_manager/tests/test_service_coverage.py',
        './brick_manager/tests/test_high_coverage_boost.py',
        './brick_manager/services/rebrickable_service.py',
        './brick_manager/services/rebrickable_sync_service.py'
    ]
    
    import ast
    all_good = True
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                ast.parse(content)
                print(f"  ✅ {file_path}")
            except SyntaxError as e:
                print(f"  ❌ {file_path}: {e}")
                all_good = False
    
    if all_good:
        print("\n✅ All files now have valid syntax!")
    else:
        print("\n❌ Some files still need fixing.")

if __name__ == "__main__":
    main()