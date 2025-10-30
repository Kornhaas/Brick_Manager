#!/usr/bin/env python3
"""
Add proper docstrings to functions and classes that are missing them.
This prevents the need for TODO docstrings that cause syntax errors.
"""

import ast
import os
import re


def add_docstring_to_function(content, func_name, line_num):
    """Add a proper docstring to a function."""
    lines = content.split('\n')
    
    # Find the function definition line
    for i, line in enumerate(lines):
        if i + 1 == line_num and f'def {func_name}(' in line:
            # Check if there's already a docstring
            next_line_idx = i + 1
            while next_line_idx < len(lines) and lines[next_line_idx].strip() == '':
                next_line_idx += 1
            
            if next_line_idx < len(lines) and '"""' in lines[next_line_idx]:
                return content  # Already has docstring
            
            # Add docstring
            indent = len(line) - len(line.lstrip()) + 4
            docstring = f'{" " * indent}"""Function: {func_name}."""'
            lines.insert(i + 1, docstring)
            return '\n'.join(lines)
    
    return content


def add_docstring_to_class(content, class_name, line_num):
    """Add a proper docstring to a class."""
    lines = content.split('\n')
    
    # Find the class definition line
    for i, line in enumerate(lines):
        if i + 1 == line_num and f'class {class_name}' in line:
            # Check if there's already a docstring
            next_line_idx = i + 1
            while next_line_idx < len(lines) and lines[next_line_idx].strip() == '':
                next_line_idx += 1
            
            if next_line_idx < len(lines) and '"""' in lines[next_line_idx]:
                return content  # Already has docstring
            
            # Add docstring
            indent = len(line) - len(line.lstrip()) + 4
            docstring = f'{" " * indent}"""Class: {class_name}."""'
            lines.insert(i + 1, docstring)
            return '\n'.join(lines)
    
    return content


def check_and_fix_file(file_path):
    """Check a file for missing docstrings and add them."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        modified = False
        
        # Check for missing module docstring
        if not ast.get_docstring(tree):
            # Add module docstring at the top
            lines = content.split('\n')
            # Find first non-comment, non-import line
            insert_idx = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""'):
                    insert_idx = i
                    break
            
            module_name = os.path.basename(file_path).replace('.py', '')
            module_docstring = f'"""\nModule: {module_name}.\n\nThis module provides functionality for the Brick Manager application.\n"""'
            lines.insert(insert_idx, module_docstring)
            content = '\n'.join(lines)
            modified = True
        
        # Check for missing function/class docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if (not ast.get_docstring(node) and 
                    not node.name.startswith('_') and 
                    not node.name.startswith('test_') and
                    node.name not in ['setUp', 'tearDown']):
                    content = add_docstring_to_function(content, node.name, node.lineno)
                    modified = True
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    content = add_docstring_to_class(content, node.name, node.lineno)
                    modified = True
        
        if modified:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"✅ Added docstrings to {file_path}")
            return True
        else:
            print(f"⚪ No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    total_files = 0
    modified_files = 0
    
    for root, dirs, files in os.walk('brick_manager'):
        # Skip test directories for now
        if 'test' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                total_files += 1
                if check_and_fix_file(file_path):
                    modified_files += 1
    
    print(f"\n🎉 Processed {total_files} files, modified {modified_files} files")


if __name__ == "__main__":
    main()