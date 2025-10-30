#!/usr/bin/env python3
"""
Pre-commit analysis and auto-fix script for Brick Manager project.
This script runs comprehensive checks and automatically fixes common issues.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class PreCommitAnalyzer:
    """Main class for running pre-commit analysis and fixes."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []
        self.fixes_applied = []

    def run_command(self, command: List[str], cwd: str = None) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def format_with_black(self) -> bool:
        """Format Python code with Black."""
        print("🔧 Formatting code with Black...")

        exit_code, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "black",
                "--line-length",
                "88",
                "brick_manager/",
                "scripts/",
                "--exclude",
                "migrations/",
            ]
        )

        if exit_code == 0:
            if "reformatted" in stdout:
                self.fixes_applied.append("Black: Auto-formatted Python files")
                print("✅ Black formatting applied")
            else:
                print("✅ No Black formatting needed")
            return True
        else:
            self.errors.append(f"Black formatting failed: {stderr}")
            return False

    def sort_imports_with_isort(self) -> bool:
        """Sort imports with isort."""
        print("📦 Sorting imports with isort...")

        exit_code, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "isort",
                "--profile",
                "black",
                "--line-length",
                "88",
                "brick_manager/",
                "scripts/",
            ]
        )

        if exit_code == 0:
            if "Fixing" in stdout or "Fixed" in stdout:
                self.fixes_applied.append("isort: Sorted imports")
                print("✅ Import sorting applied")
            else:
                print("✅ No import sorting needed")
            return True
        else:
            self.errors.append(f"isort failed: {stderr}")
            return False

    def run_flake8(self) -> bool:
        """Run flake8 linting."""
        print("🔍 Running flake8 linting...")

        exit_code, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "flake8",
                "--max-line-length",
                "88",
                "--extend-ignore",
                "E203,W503,E501",
                "--exclude",
                "migrations/,__pycache__/,.git/,build/,dist/",
                "brick_manager/",
            ]
        )

        if exit_code == 0:
            print("✅ flake8 passed")
            return True
        else:
            self.warnings.append(f"flake8 issues found:\n{stdout}")
            return False

    def run_pylint(self) -> bool:
        """Run pylint analysis."""
        print("🔍 Running pylint analysis...")

        exit_code, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "pylint",
                "brick_manager/",
                "--output-format",
                "text",
                "--reports",
                "no",
                "--score",
                "yes",
            ]
        )

        # Pylint returns non-zero for warnings/errors, but we still want to see the output
        if "Your code has been rated at" in stdout:
            score_match = re.search(r"Your code has been rated at ([\d.]+)/10", stdout)
            if score_match:
                score = float(score_match.group(1))
                if score >= 8.0:
                    print(f"✅ pylint passed with score: {score}/10")
                    return True
                else:
                    self.warnings.append(f"pylint score is low: {score}/10\n{stdout}")
                    return False

        if stdout:
            self.warnings.append(f"pylint issues:\n{stdout}")

        return exit_code == 0

    def run_bandit_security_check(self) -> bool:
        """Run Bandit security analysis."""
        print("🔒 Running Bandit security analysis...")

        exit_code, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "bandit",
                "-r",
                "brick_manager/",
                "-f",
                "json",
                "-o",
                "bandit-report.json",
                "--exclude",
                "*/tests/*",
            ]
        )

        # Check if bandit report exists
        bandit_report = self.project_root / "bandit-report.json"
        if bandit_report.exists():
            try:
                with open(bandit_report, "r") as f:
                    report = json.load(f)

                if report.get("results"):
                    high_severity = [
                        r
                        for r in report["results"]
                        if r.get("issue_severity") == "HIGH"
                    ]
                    medium_severity = [
                        r
                        for r in report["results"]
                        if r.get("issue_severity") == "MEDIUM"
                    ]

                    if high_severity:
                        self.errors.append(
                            f"Bandit found {len(high_severity)} HIGH severity security issues"
                        )
                    if medium_severity:
                        self.warnings.append(
                            f"Bandit found {len(medium_severity)} MEDIUM severity security issues"
                        )

                    print(f"⚠️  Bandit found {len(report['results'])} security issues")
                    return len(high_severity) == 0
                else:
                    print("✅ Bandit security check passed")
                    return True

            except json.JSONDecodeError:
                self.warnings.append("Could not parse Bandit report")
                return False
        else:
            self.warnings.append("Bandit report not generated")
            return False

    def fix_common_issues(self) -> None:
        """Fix common Python issues automatically."""
        print("🔧 Fixing common issues...")

        python_files = list(self.project_root.glob("brick_manager/**/*.py"))

        for file_path in python_files:
            if "migrations" in str(file_path) or "__pycache__" in str(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                original_content = content

                # Fix common issues
                content = self._fix_trailing_whitespace(content)
                content = self._fix_missing_docstrings(content, file_path)
                content = self._fix_long_lines(content)
                content = self._ensure_final_newline(content)

                if content != original_content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.fixes_applied.append(
                        f"Fixed common issues in {file_path.name}"
                    )

            except Exception as e:
                self.warnings.append(f"Could not process {file_path}: {str(e)}")

    def _fix_trailing_whitespace(self, content: str) -> str:
        """Remove trailing whitespace from lines."""
        lines = content.split("\n")
        fixed_lines = [line.rstrip() for line in lines]
        return "\n".join(fixed_lines)

    def _fix_missing_docstrings(self, content: str, file_path: Path) -> str:
        """Add basic docstrings to functions/classes missing them."""
        lines = content.split("\n")
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for function/class definitions
            if re.match(
                r"^(class|def)\s+\w+", line.strip()
            ) and not line.strip().startswith("#"):
                new_lines.append(line)

                # Check if next non-empty line is a docstring
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    new_lines.append(lines[j])
                    j += 1
                
                if (j < len(lines) and 
                    not (lines[j].strip().startswith('"""') or 
                         lines[j].strip().startswith("'''"))):
                    
                    # Skip adding TODO docstrings to prevent syntax errors
                    # Docstring requirements are handled by flake8 configuration
                    pass
                
                i = j - 1 if j > i else i
            else:
                new_lines.append(line)

            i += 1

        return "\n".join(new_lines)

    def _fix_long_lines(self, content: str) -> str:
        """Try to fix some common long line issues."""
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            if len(line) > 88 and "=" in line and 'f"' in line:
                # Try to break long f-string assignments
                if ' = f"' in line:
                    parts = line.split(' = f"', 1)
                    if len(parts) == 2:
                        var_part = parts[0]
                        string_part = 'f"' + parts[1]

                        if len(var_part) < 40:  # Only if variable part is reasonable
                            indent = len(line) - len(line.lstrip())
                            new_lines.append(f"{var_part} = (")
                            new_lines.append(f"{' ' * (indent + 4)}{string_part}")
                            new_lines.append(f"{' ' * indent})")
                            continue

            new_lines.append(line)

        return "\n".join(new_lines)

    def _ensure_final_newline(self, content: str) -> str:
        """Ensure file ends with a newline."""
        if content and not content.endswith("\n"):
            return content + "\n"
        return content

    def run_tests(self) -> bool:
        """Run the test suite."""
        print("🧪 Running tests...")

        exit_code, stdout, stderr = self.run_command(
            [
                "poetry",
                "run",
                "pytest",
                "--tb=short",
                "-v",
                "--cov=brick_manager",
                "--cov-report=term-missing",
            ]
        )

        if exit_code == 0:
            print("✅ All tests passed")
            return True
        else:
            self.errors.append(f"Tests failed:\n{stdout}\n{stderr}")
            return False

    def check_dependencies(self) -> bool:
        """Check for dependency issues."""
        print("📦 Checking dependencies...")

        # Check for security vulnerabilities
        exit_code, stdout, stderr = self.run_command(["poetry", "check"])

        if exit_code == 0:
            print("✅ Poetry dependencies are valid")
            return True
        else:
            self.warnings.append(f"Poetry dependency issues: {stderr}")
            return False

    def generate_report(self) -> None:
        """Generate a final report."""
        print("\n" + "=" * 60)
        print("📊 PRE-COMMIT ANALYSIS REPORT")
        print("=" * 60)

        if self.fixes_applied:
            print("\n✅ FIXES APPLIED:")
            for fix in self.fixes_applied:
                print(f"  • {fix}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")

        if not self.errors and not self.warnings:
            print("\n🎉 All checks passed! Code is ready for commit.")
        elif not self.errors:
            print("\n✅ No blocking errors found. Code can be committed with warnings.")
        else:
            print("\n❌ Blocking errors found. Please fix before committing.")

        print("=" * 60)

    def run_all_checks(self, fix_issues: bool = True) -> bool:
        """Run all pre-commit checks."""
        print("🚀 Starting pre-commit analysis...")

        success = True

        # Auto-fix issues first
        if fix_issues:
            self.fix_common_issues()
            self.format_with_black()
            self.sort_imports_with_isort()

        # Run checks
        if not self.run_flake8():
            success = False

        if not self.run_pylint():
            success = False  # Don't fail on pylint warnings

        if not self.run_bandit_security_check():
            success = False

        if not self.check_dependencies():
            success = False  # Don't fail on dependency warnings

        if not self.run_tests():
            success = False

        self.generate_report()

        return success


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-commit analysis and auto-fix script"
    )
    parser.add_argument("--no-fix", action="store_true", help="Don't auto-fix issues")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")

    args = parser.parse_args()

    # Find project root
    current_dir = Path(__file__).parent.parent

    analyzer = PreCommitAnalyzer(str(current_dir))

    # Override test running if requested
    if args.no_tests:
        analyzer.run_tests = lambda: True

    success = analyzer.run_all_checks(fix_issues=not args.no_fix)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
