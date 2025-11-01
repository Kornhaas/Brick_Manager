#!/usr/bin/env python3
"""
Critical flake8 fixes for undefined variables and syntax errors.
This script fixes F821 undefined variables and other critical issues.
"""

import os
import re
from pathlib import Path


class CriticalFlake8Fixer:
    """Fix critical flake8 issues that break functionality."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def fix_undefined_variables(self, file_path: Path) -> bool:
        """Fix F821 undefined variable issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            
            # Fix common pattern: _result = something; result.method() -> result = something; result.method()
            # Pattern 1: _result = ... followed by result usage
            def fix_result_underscore(match):
                lines = match.group(0).split('\n')
                fixed_lines = []
                for line in lines:
                    # Change _result = to result =
                    if '_result =' in line and 'result' not in line.replace('_result', ''):
                        line = line.replace('_result =', 'result =')
                    # Change _response = to response =
                    elif '_response =' in line and 'response' not in line.replace('_response', ''):
                        line = line.replace('_response =', 'response =')
                    fixed_lines.append(line)
                return '\n'.join(fixed_lines)

            # Find blocks with _result = followed by result usage
            content = re.sub(
                r'(\s+)_result\s*=\s*[^\n]+\n((?:\s*[^\n]*result[^\n]*\n?)*)',
                lambda m: fix_result_underscore(m.group(0)),
                content
            )
            
            # Find blocks with _response = followed by response usage  
            content = re.sub(
                r'(\s+)_response\s*=\s*[^\n]+\n((?:\s*[^\n]*response[^\n]*\n?)*)',
                lambda m: fix_result_underscore(m.group(0)),
                content
            )

            # Fix specific patterns where variables are used after being assigned with underscore
            patterns_to_fix = [
                (r'(\s+)_result\s*=\s*([^\n]+)\n(\s+)result\.', r'\1result = \2\n\3result.'),
                (r'(\s+)_response\s*=\s*([^\n]+)\n(\s+)response\.', r'\1response = \2\n\3response.'),
                (r'(\s+)_result\s*=\s*([^\n]+)\n(\s+)assert.*result', r'\1result = \2\n\3assert result'),
            ]
            
            for pattern, replacement in patterns_to_fix:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            print(f"❌ Error fixing undefined variables in {file_path}: {e}")

        return False

    def fix_unused_variables(self, file_path: Path) -> bool:
        """Fix F841 unused variable issues by adding underscores."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            
            # Add underscore prefix to variables that are assigned but never used
            # Pattern: variable = something (where variable is not used elsewhere)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                # Look for assignment patterns
                if '=' in line and not line.strip().startswith('#'):
                    # Extract variable name from assignment
                    match = re.match(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*', line)
                    if match:
                        indent = match.group(1)
                        var_name = match.group(2)
                        
                        # Skip if already starts with underscore
                        if var_name.startswith('_'):
                            continue
                            
                        # Check if this variable is used elsewhere in the function
                        # Look for the variable in subsequent lines until next function/class
                        used_elsewhere = False
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith(('def ', 'class ', '@')):
                                break
                            if var_name in lines[j] and '=' not in lines[j].split(var_name)[0]:
                                used_elsewhere = True
                                break
                        
                        # If not used elsewhere, add underscore prefix
                        if not used_elsewhere and var_name in ['result', 'response', 'mock_file', 'mock_app', 'mock_db', 'security_headers', 'expected_blueprints', 'path_result']:
                            lines[i] = line.replace(f'{var_name} =', f'_{var_name} =', 1)

            new_content = '\n'.join(lines)
            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True

        except Exception as e:
            print(f"❌ Error fixing unused variables in {file_path}: {e}")

        return False

    def fix_import_order(self, file_path: Path) -> bool:
        """Fix basic import order issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            
            # Basic fix: ensure stdlib imports come before third-party
            lines = content.split('\n')
            import_lines = []
            other_lines = []
            import_section = True
            
            for line in lines:
                if import_section and (line.startswith('import ') or line.startswith('from ')):
                    import_lines.append(line)
                elif import_section and line.strip() == '':
                    import_lines.append(line)
                else:
                    if import_section:
                        import_section = False
                    other_lines.append(line)
            
            # Separate stdlib and third-party imports
            stdlib_imports = []
            thirdparty_imports = []
            
            stdlib_modules = {
                'os', 'sys', 'json', 'sqlite3', 'datetime', 'logging', 'tempfile', 
                'pathlib', 'typing', 'unittest', 'io', 'gc', 'atexit'
            }
            
            for line in import_lines:
                if line.strip() == '':
                    continue
                    
                # Check if it's a stdlib import
                is_stdlib = False
                if line.startswith('import '):
                    module = line.replace('import ', '').split('.')[0].split(' as ')[0].strip()
                    if module in stdlib_modules:
                        is_stdlib = True
                elif line.startswith('from '):
                    module = line.split(' ')[1].split('.')[0]
                    if module in stdlib_modules:
                        is_stdlib = True
                
                if is_stdlib:
                    stdlib_imports.append(line)
                else:
                    thirdparty_imports.append(line)
            
            # Rebuild with proper order
            if stdlib_imports and thirdparty_imports:
                new_imports = stdlib_imports + [''] + thirdparty_imports + ['']
                new_content = '\n'.join(new_imports + other_lines)
                
                if new_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    return True

        except Exception as e:
            print(f"❌ Error fixing imports in {file_path}: {e}")

        return False

    def run_critical_fixes(self) -> bool:
        """Run critical fixes on all Python files."""
        print("🔧 Running critical flake8 fixes...")
        
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
            
            # Fix undefined variables first (critical)
            if self.fix_undefined_variables(file_path):
                file_fixes += 1
            
            # Fix unused variables
            if self.fix_unused_variables(file_path):
                file_fixes += 1
            
            # Fix import order
            if self.fix_import_order(file_path):
                file_fixes += 1
            
            if file_fixes > 0:
                print(f"✅ Fixed {file_fixes} critical issues in {file_path.relative_to(self.project_root)}")
                total_fixes += file_fixes
        
        print(f"\n📊 Critical fixes summary: {total_fixes} issues fixed")
        return True


def main():
    """Main function."""
    project_root = Path.cwd()
    fixer = CriticalFlake8Fixer(str(project_root))
    
    try:
        fixer.run_critical_fixes()
        print("\n🎉 Critical fixes completed!")
        print("💡 Run 'poetry run flake8 brick_manager/' to check remaining issues.")
        
    except Exception as e:
        print(f"\n❌ Error during critical fixes: {e}")


if __name__ == "__main__":
    main()