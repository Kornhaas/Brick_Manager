#!/usr/bin/env python3
"""
Advanced flake8 fixes for remaining issues.
This script handles the specific remaining issues found in the codebase.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List


class AdvancedFlake8Fixer:
    """Fix specific remaining flake8 issues."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.fixes_applied = []

    def fix_docstring_formatting(self, file_path: Path) -> int:
        """Fix D200, D202, D205, D400, D401 docstring issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes = 0

            # D200: One-line docstring should fit on one line with quotes
            # Find multi-line docstrings that are actually one line
            def fix_one_line_docstring(match):
                docstring = match.group(1).strip()
                if '\n' not in docstring and len(docstring) <= 70:
                    return f'"""{docstring}"""'
                return match.group(0)
            
            content = re.sub(r'"""\s*([^"]+?)\s*"""', fix_one_line_docstring, content, flags=re.DOTALL)

            # D202: No blank lines allowed after function docstring
            # Remove blank lines immediately after docstrings
            content = re.sub(
                r'(""".+?"""\s*)\n\s*\n(\s*(?:def|class|if|for|while|try|with|@))',
                r'\1\n\2',
                content,
                flags=re.DOTALL
            )

            # D205: 1 blank line required between summary line and description
            def fix_docstring_blank_line(match):
                full_docstring = match.group(1)
                lines = full_docstring.split('\n')
                if len(lines) > 2:
                    # If first line is summary and second line has content without blank line
                    if lines[1].strip() and not lines[1].strip().startswith('"""'):
                        lines.insert(1, '')
                        return '"""' + '\n'.join(lines) + '"""'
                return match.group(0)
            
            content = re.sub(r'"""(.*?)"""', fix_docstring_blank_line, content, flags=re.DOTALL)

            # D400: First line should end with a period
            def add_period_to_first_line(match):
                docstring_content = match.group(1)
                lines = docstring_content.split('\n')
                if lines and lines[0].strip() and not lines[0].strip().endswith('.'):
                    lines[0] = lines[0].rstrip() + '.'
                    return '"""' + '\n'.join(lines) + '"""'
                return match.group(0)
            
            content = re.sub(r'"""(.*?)"""', add_period_to_first_line, content, flags=re.DOTALL)

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixes += 1

            return fixes

        except Exception as e:
            print(f"❌ Error fixing docstrings in {file_path}: {e}")
            return 0

    def fix_line_length(self, file_path: Path) -> int:
        """Fix E501 line too long issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            
            for i, line in enumerate(lines):
                if len(line.rstrip()) > 79:
                    # Try to break long lines at logical points
                    stripped = line.rstrip()
                    indent = len(line) - len(line.lstrip())
                    
                    # Break long import lines
                    if 'import' in stripped and ',' in stripped:
                        if 'from' in stripped:
                            # from module import a, b, c -> from module import (a, b, c)
                            match = re.match(r'(\s*from\s+\S+\s+import\s+)(.+)', stripped)
                            if match:
                                prefix = match.group(1)
                                imports = match.group(2)
                                if not imports.startswith('('):
                                    new_line = f"{prefix}(\n{' ' * (indent + 4)}{imports}\n{' ' * indent})"
                                    lines[i] = new_line + '\n'
                                    modified = True
                                    continue
                    
                    # Break long function calls/definitions
                    if '(' in stripped and ')' in stripped and '=' in stripped:
                        # Try to break at commas within function calls
                        parts = stripped.split(',')
                        if len(parts) > 1:
                            new_line = parts[0] + ',\n'
                            for j, part in enumerate(parts[1:], 1):
                                if j == len(parts) - 1:
                                    new_line += ' ' * (indent + 4) + part.strip()
                                else:
                                    new_line += ' ' * (indent + 4) + part.strip() + ',\n'
                            
                            if len(new_line.split('\n')[0]) <= 79:
                                lines[i] = new_line + '\n'
                                modified = True
                                continue
                    
                    # Break long string concatenations
                    if ' + ' in stripped and '"' in stripped:
                        parts = stripped.split(' + ')
                        if len(parts) > 1:
                            new_line = parts[0] + ' + \\\n'
                            for part in parts[1:]:
                                new_line += ' ' * (indent + 4) + part + ' + \\\n'
                            new_line = new_line.rstrip(' + \\\n')
                            
                            lines[i] = new_line + '\n'
                            modified = True
                            continue

            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return 1

        except Exception as e:
            print(f"❌ Error fixing line length in {file_path}: {e}")
            
        return 0

    def fix_unused_variables(self, file_path: Path) -> int:
        """Fix F841 local variable assigned but never used."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Add underscore prefix to unused variables in common patterns
            # Pattern: variable = something (but variable never used again)
            patterns = [
                r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*.*mock.*\(',  # mock variables
                r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*.*patch\(',   # patch variables
                r'(\s+)(result)\s*=\s*.*\(',                        # result variables
                r'(\s+)(response)\s*=\s*.*\(',                      # response variables
            ]
            
            for pattern in patterns:
                def replace_unused_var(match):
                    indent = match.group(1)
                    var_name = match.group(2)
                    rest = match.group(0)[len(indent + var_name):]
                    return f"{indent}_{var_name}{rest}"
                
                content = re.sub(pattern, replace_unused_var, content)

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return 1

        except Exception as e:
            print(f"❌ Error fixing unused variables in {file_path}: {e}")
            
        return 0

    def run_advanced_fixes(self) -> bool:
        """Run advanced fixes on all Python files."""
        print("🔧 Running advanced flake8 fixes...")
        
        brick_manager_path = self.project_root / "brick_manager"
        if not brick_manager_path.exists():
            print(f"❌ brick_manager directory not found")
            return False
        
        python_files = []
        for root, dirs, files in os.walk(brick_manager_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        total_fixes = 0
        
        for file_path in python_files:
            file_fixes = 0
            
            # Fix docstring issues
            file_fixes += self.fix_docstring_formatting(file_path)
            
            # Fix line length issues  
            file_fixes += self.fix_line_length(file_path)
            
            # Fix unused variables
            file_fixes += self.fix_unused_variables(file_path)
            
            if file_fixes > 0:
                print(f"✅ Fixed {file_fixes} advanced issues in {file_path.relative_to(self.project_root)}")
                total_fixes += file_fixes
        
        print(f"\n📊 Advanced fixes summary: {total_fixes} issues fixed")
        return True


def main():
    """Main function."""
    project_root = Path.cwd()
    fixer = AdvancedFlake8Fixer(str(project_root))
    
    try:
        fixer.run_advanced_fixes()
        
        # Run isort and black again to clean up
        print("\n🔧 Running final cleanup...")
        subprocess.run(["poetry", "run", "isort", "brick_manager/"], capture_output=True)
        subprocess.run(["poetry", "run", "black", "brick_manager/"], capture_output=True)
        
        print("\n🎉 Advanced fixes completed!")
        print("💡 Run 'poetry run flake8 brick_manager/' to check remaining issues.")
        
    except Exception as e:
        print(f"\n❌ Error during advanced fixes: {e}")


if __name__ == "__main__":
    main()