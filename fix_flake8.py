#!/usr/bin/env python3
"""
Automated flake8 fixes for Brick Manager project.
This script fixes the most common and safe flake8 issues automatically.
"""

import ast
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set


class Flake8AutoFixer:
    """Automatically fix common flake8 issues."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.fixes_applied = []

    def run_command(self, command: List[str]) -> tuple:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def fix_imports_with_isort(self) -> bool:
        """Fix import order issues with isort."""
        print("🔧 Fixing import order with isort...")
        
        exit_code, stdout, stderr = self.run_command([
            "poetry", "run", "isort", 
            "--profile", "black",
            "--line-length", "88",
            "--multi-line", "3",
            "--trailing-comma",
            "--force-grid-wrap", "0",
            "--combine-as",
            "--use-parentheses",
            "brick_manager/"
        ])
        
        if exit_code == 0:
            print("✅ Import order fixed with isort")
            self.fixes_applied.append("Import order (isort)")
            return True
        else:
            print(f"❌ isort failed: {stderr}")
            return False

    def fix_unused_imports(self) -> bool:
        """Remove unused imports using autoflake."""
        print("🔧 Removing unused imports with autoflake...")
        
        exit_code, stdout, stderr = self.run_command([
            "poetry", "run", "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--ignore-init-module-imports",
            "--in-place",
            "--recursive",
            "brick_manager/"
        ])
        
        if exit_code == 0:
            print("✅ Unused imports removed with autoflake")
            self.fixes_applied.append("Unused imports (autoflake)")
            return True
        else:
            print(f"❌ autoflake failed: {stderr}")
            return False

    def fix_docstring_issues(self, file_path: Path) -> bool:
        """Fix common docstring formatting issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix D200: One-line docstring should fit on one line with quotes
            content = re.sub(
                r'"""([^"\n]{1,80})"""\s*\n\s*"""',
                r'"""\1"""',
                content
            )
            
            # Fix D205: 1 blank line required between summary line and description
            content = re.sub(
                r'("""\s*[^\n]+)\n(\s*[^\s"])',
                r'\1\n\n\2',
                content
            )
            
            # Fix D400: First line should end with a period
            def add_period_to_docstring(match):
                docstring = match.group(1)
                if not docstring.strip().endswith('.'):
                    return f'"""{docstring.strip()}."""'
                return match.group(0)
            
            content = re.sub(
                r'"""([^"\n]+)"""',
                add_period_to_docstring,
                content
            )
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            print(f"❌ Error fixing docstrings in {file_path}: {e}")
            
        return False

    def fix_f_string_issues(self, file_path: Path) -> bool:
        """Fix F541: f-string is missing placeholders."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Find f-strings without placeholders and convert to regular strings
            # Pattern: f"text without {variables}"
            def fix_empty_fstring(match):
                quote_char = match.group(1)
                string_content = match.group(2)
                # If no {} placeholders, remove f prefix
                if '{' not in string_content:
                    return f'{quote_char}{string_content}{quote_char}'
                return match.group(0)
            
            # Handle both single and double quotes
            content = re.sub(r'f(["\'])([^"\']*?)\1', fix_empty_fstring, content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            print(f"❌ Error fixing f-strings in {file_path}: {e}")
            
        return False

    def fix_comparison_issues(self, file_path: Path) -> bool:
        """Fix E712: comparison to False should be 'if cond is False:' or 'if not cond:'."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix == False comparisons
            content = re.sub(r'(\w+)\s*==\s*False', r'\1 is False', content)
            content = re.sub(r'(\w+)\s*!=\s*False', r'\1 is not False', content)
            content = re.sub(r'(\w+)\s*==\s*True', r'\1 is True', content)
            content = re.sub(r'(\w+)\s*!=\s*True', r'\1 is not True', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            print(f"❌ Error fixing comparisons in {file_path}: {e}")
            
        return False

    def fix_bare_except(self, file_path: Path) -> bool:
        """Fix E722: do not use bare 'except'."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace bare except with except Exception
            content = re.sub(r'\bexcept:\s*\n', 'except Exception:\n', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            print(f"❌ Error fixing bare except in {file_path}: {e}")
            
        return False

    def fix_file(self, file_path: Path) -> int:
        """Fix issues in a single file."""
        fixes_count = 0
        
        if self.fix_docstring_issues(file_path):
            fixes_count += 1
            
        if self.fix_f_string_issues(file_path):
            fixes_count += 1
            
        if self.fix_comparison_issues(file_path):
            fixes_count += 1
            
        if self.fix_bare_except(file_path):
            fixes_count += 1
            
        return fixes_count

    def fix_all_files(self) -> int:
        """Fix issues in all Python files."""
        total_fixes = 0
        
        # Find all Python files in brick_manager directory
        brick_manager_path = self.project_root / "brick_manager"
        if not brick_manager_path.exists():
            print(f"❌ brick_manager directory not found at {brick_manager_path}")
            # Try to find the actual directory
            for item in self.project_root.iterdir():
                if item.is_dir() and 'brick' in item.name.lower():
                    print(f"📂 Found directory: {item}")
            return 0
            
        python_files = []
        for root, dirs, files in os.walk(brick_manager_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        print(f"🔧 Processing {len(python_files)} Python files...")
        
        for file_path in python_files:
            fixes = self.fix_file(file_path)
            if fixes > 0:
                print(f"✅ Fixed {fixes} issues in {file_path.relative_to(self.project_root)}")
                total_fixes += fixes
        
        return total_fixes

    def run_final_formatting(self) -> bool:
        """Run final formatting with black."""
        print("🔧 Running final formatting with black...")
        
        exit_code, stdout, stderr = self.run_command([
            "poetry", "run", "black", 
            "--line-length", "88",
            "brick_manager/"
        ])
        
        if exit_code == 0:
            print("✅ Final formatting completed")
            return True
        else:
            print(f"❌ Black formatting failed: {stderr}")
            return False

    def run_fixes(self) -> bool:
        """Run all automated fixes."""
        print("🚀 Starting automated flake8 fixes...")
        
        # Step 1: Fix import order
        self.fix_imports_with_isort()
        
        # Step 2: Remove unused imports
        self.fix_unused_imports()
        
        # Step 3: Fix individual file issues
        file_fixes = self.fix_all_files()
        
        # Step 4: Final formatting
        self.run_final_formatting()
        
        print(f"\n📊 Summary:")
        print(f"  - Applied {len(self.fixes_applied)} global fixes")
        print(f"  - Fixed {file_fixes} individual file issues")
        
        for fix in self.fixes_applied:
            print(f"  ✅ {fix}")
            
        return True


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python fix_flake8.py")
        print("Automatically fixes common flake8 issues in the Brick Manager project.")
        return
    
    # Use current working directory
    project_root = Path.cwd()
    print(f"🔍 Working in: {project_root}")
    fixer = Flake8AutoFixer(str(project_root))
    
    try:
        fixer.run_fixes()
        print("\n🎉 Automated fixes completed!")
        print("💡 Run 'make lint' to check remaining issues.")
        
    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during fixes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()