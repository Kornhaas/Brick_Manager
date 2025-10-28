#!/usr/bin/env python3
"""Fix malformed function definitions with TODO docstrings in parameter lists."""

import re
import os

def fix_malformed_functions(file_path):
    """Fix malformed function definitions with TODO docstrings."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find functions with TODO docstrings in parameter lists
    # This handles multi-line function definitions
    pattern = r'(def\s+\w+\s*\([^)]*?)\s*"""TODO:[^"]*"""\s*([^)]*?\)[^:]*:)'
    
    def replacement(match):
        func_start = match.group(1).strip()
        func_end = match.group(2).strip()
        # Remove any trailing comma and whitespace from func_start
        func_start = re.sub(r',\s*$', '', func_start)
        return f'{func_start}\n        {func_end}'
    
    # Apply the fix
    fixed_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also handle TODO docstrings that are on their own lines within function definitions
    lines = fixed_content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line contains a TODO docstring that should be removed
        if '"""TODO: Add docstring for' in line and line.strip().startswith('"""'):
            # Skip this line
            i += 1
            continue
            
        fixed_lines.append(line)
        i += 1
    
    fixed_content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed {file_path}")

# Fix the problematic files
fix_malformed_functions('/workspaces/Brick_Manager/brick_manager/services/rebrickable_service.py')
fix_malformed_functions('/workspaces/Brick_Manager/brick_manager/services/rebrickable_sync_service.py')

print("Syntax fixes applied")