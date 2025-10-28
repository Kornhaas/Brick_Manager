#!/usr/bin/env python3
"""Script to fix syntax errors in test files."""

import re
import os

def fix_docstring_syntax_errors(file_path):
    """Fix TODO docstrings that are incorrectly placed in function signatures."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find malformed function definitions with TODO docstrings
    pattern = r'(def [^:]+),\s*\n\s*"""TODO:[^"]*"""\s*\n\s*([^)]+)\):'
    
    def replacement(match):
        func_start = match.group(1)
        params_end = match.group(2)
        return f'{func_start},\n                                   {params_end}):'
    
    content = re.sub(pattern, replacement, content)
    
    # Also handle cases where the TODO is on the same line
    pattern2 = r'(def [^,]+),\s*"""TODO:[^"]*"""\s*([^:]+):'
    def replacement2(match):
        func_start = match.group(1)
        params_end = match.group(2)
        return f'{func_start}, {params_end}):'
    
    content = re.sub(pattern2, replacement2, content)
    
    with open(file_path, 'w') as f:
        f.write(content)

# Fix all test files
test_dir = '/workspaces/Brick_Manager/brick_manager/tests'
for filename in os.listdir(test_dir):
    if filename.endswith('.py'):
        file_path = os.path.join(test_dir, filename)
        fix_docstring_syntax_errors(file_path)

# Also fix services that might have similar issues
services_dir = '/workspaces/Brick_Manager/brick_manager/services'
for filename in os.listdir(services_dir):
    if filename.endswith('.py'):
        file_path = os.path.join(services_dir, filename)
        fix_docstring_syntax_errors(file_path)

print("Fixed syntax errors in test and service files")