#!/usr/bin/env python3
"""
Custom security checks for the Brick Manager project.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class SecurityChecker(ast.NodeVisitor):
    """AST visitor to check for security issues."""

    def __init__(self):
        self.issues = []

    def visit_Call(self, node):
        """Check function calls for security issues."""
        if isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "execute"
                and isinstance(node.func.value, ast.Name)
                and "session" in node.func.value.id.lower()
            ):
                # Check for SQL injection risks
                for arg in node.args:
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                        self.issues.append(
                            (
                                node.lineno,
                                "Potential SQL injection: Use parameterized queries instead of string formatting",
                            )
                        )

        if isinstance(node.func, ast.Name):
            # Check for unsafe eval/exec usage
            if node.func.id in ["eval", "exec"]:
                self.issues.append(
                    (
                        node.lineno,
                        f"Unsafe use of {node.func.id}() - avoid dynamic code execution",
                    )
                )

            # Check for unsafe pickle usage
            if node.func.id in ["loads", "load"] and len(node.args) > 0:
                self.issues.append(
                    (
                        node.lineno,
                        "Potential unsafe deserialization - validate data sources",
                    )
                )

        self.generic_visit(node)

    def visit_Import(self, node):
        """Check imports for security issues."""
        for alias in node.names:
            if alias.name in ["pickle", "cPickle"]:
                self.issues.append(
                    (
                        node.lineno,
                        "Using pickle module - ensure data comes from trusted sources",
                    )
                )

    def visit_ImportFrom(self, node):
        """Check from imports for security issues."""
        if node.module in ["pickle", "cPickle"]:
            self.issues.append(
                (
                    node.lineno,
                    "Using pickle module - ensure data comes from trusted sources",
                )
            )


def check_file(file_path: Path) -> List[Tuple[int, str]]:
    """Check a single Python file for security issues."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        checker = SecurityChecker()
        checker.visit(tree)

        return checker.issues
    except Exception as e:
        return [(0, f"Error parsing file: {str(e)}")]


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: security_check.py <file1> [file2] ...")
        sys.exit(1)

    total_issues = 0

    for file_path in sys.argv[1:]:
        path = Path(file_path)
        if not path.exists() or not path.suffix == ".py":
            continue

        issues = check_file(path)

        if issues:
            print(f"\n🔒 Security issues in {file_path}:")
            for line_no, message in issues:
                if line_no > 0:
                    print(f"  Line {line_no}: {message}")
                else:
                    print(f"  {message}")
            total_issues += len(issues)

    if total_issues > 0:
        print(f"\n❌ Found {total_issues} security issues")
        sys.exit(1)
    else:
        print("✅ No security issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
