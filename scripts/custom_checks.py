#!/usr/bin/env python3
"""
Custom Python code checks for the Brick Manager project.
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple


class CustomChecker(ast.NodeVisitor):
    """AST visitor for custom code quality checks."""

    def __init__(self, content: str):
        self.content = content
        self.lines = content.split("\n")
        self.issues = []

    def visit_FunctionDef(self, node):
        """Check function definitions."""
        # Check for functions with too many arguments
        if len(node.args.args) > 6:
            self.issues.append(
                (
                    node.lineno,
                    f"Function '{node.name}' has {len(node.args.args)} parameters. Consider reducing complexity.",
                )
            )

        # Check for missing docstrings
        if (
            not ast.get_docstring(node)
            and not node.name.startswith("_")
            and node.name not in ["setUp", "tearDown", "test_"]
        ):
            self.issues.append(
                (node.lineno, f"Function '{node.name}' is missing a docstring")
            )

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Check class definitions."""
        # Check for missing docstrings
        if not ast.get_docstring(node):
            self.issues.append(
                (node.lineno, f"Class '{node.name}' is missing a docstring")
            )

        self.generic_visit(node)

    def visit_Try(self, node):
        """Check try/except blocks."""
        for handler in node.handlers:
            if handler.type is None:
                self.issues.append(
                    (handler.lineno, "Bare except clause - specify exception types")
                )
            elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                self.issues.append(
                    (handler.lineno, "Catching generic 'Exception' - be more specific")
                )

        self.generic_visit(node)


def check_file_content(file_path: Path) -> List[Tuple[int, str]]:
    """Check file content for various issues."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return [(0, f"Could not read file: {file_path}")]

    issues = []
    lines = content.split("\n")

    # Check for long lines
    for i, line in enumerate(lines, 1):
        if len(line) > 88 and not line.strip().startswith("#"):
            issues.append((i, f"Line too long ({len(line)} > 88 characters)"))

    # Check for TODO/FIXME comments
    for i, line in enumerate(lines, 1):
        if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line, re.IGNORECASE):
            issues.append((i, "TODO/FIXME comment found - consider addressing"))

    # Check for print statements (should use logging)
    for i, line in enumerate(lines, 1):
        if (
            re.search(r"\bprint\s*\(", line)
            and not line.strip().startswith("#")
            and "test_" not in str(file_path)
        ):
            issues.append((i, "Consider using logging instead of print()"))

    # AST-based checks
    try:
        tree = ast.parse(content)
        checker = CustomChecker(content)
        checker.visit(tree)
        issues.extend(checker.issues)
    except SyntaxError as e:
        issues.append((e.lineno or 0, f"Syntax error: {e.msg}"))

    return issues


def check_imports(file_path: Path) -> List[Tuple[int, str]]:
    """Check import statements for best practices."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return []

    issues = []
    lines = content.split("\n")
    imports_section = True

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check if we're still in imports section
        if stripped and not stripped.startswith(
            ("import ", "from ", "#", '"""', "'''")
        ):
            imports_section = False

        # Check for star imports
        if stripped.startswith("from ") and " import *" in stripped:
            issues.append((i, "Avoid star imports - import specific items"))

        # Check for relative imports that could be absolute
        if stripped.startswith("from .") and imports_section:
            issues.append((i, "Consider using absolute imports for clarity"))

    return issues


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: custom_checks.py <file1> [file2] ...")
        sys.exit(1)

    total_issues = 0

    for file_path in sys.argv[1:]:
        path = Path(file_path)
        if not path.exists() or path.suffix != ".py":
            continue

        # Skip test files and migrations
        if "test_" in path.name or "migrations" in str(path):
            continue

        issues = []
        issues.extend(check_file_content(path))
        issues.extend(check_imports(path))

        if issues:
            print(f"\n🔍 Code quality issues in {file_path}:")
            for line_no, message in sorted(issues):
                if line_no > 0:
                    print(f"  Line {line_no}: {message}")
                else:
                    print(f"  {message}")
            total_issues += len(issues)

    if total_issues > 0:
        print(f"\n⚠️  Found {total_issues} code quality issues")
        # Don't fail the commit for code quality issues, just warn
        sys.exit(0)
    else:
        print("✅ No code quality issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
