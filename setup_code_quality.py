#!/usr/bin/env python3
"""
Simple flake8 configuration and maintenance script.
This creates a .flake8 config file with reasonable exclusions for this project.
"""

from pathlib import Path


def create_flake8_config():
    """Create a .flake8 configuration file with reasonable settings."""
    config_content = """[flake8]
# Maximum line length
max-line-length = 88

# Error codes to ignore
ignore = 
    # Line too long (handled by black)
    E501,
    # Whitespace before ':' (handled by black)
    E203,
    # Line break before binary operator (handled by black)
    W503,
    # Missing docstring in public module
    D100,
    # Missing docstring in public class
    D101,
    # Missing docstring in public method
    D102,
    # Missing docstring in public function
    D103,
    # Missing docstring in public package
    D104,
    # Missing docstring in magic method
    D105,
    # Missing docstring in public nested class
    D106,
    # Missing docstring in __init__
    D107,
    # One-line docstring should fit on one line
    D200,
    # No blank lines allowed after function docstring
    D202,
    # 1 blank line required between summary line and description
    D205,
    # First line should end with a period
    D400,
    # First line should be in imperative mood
    D401,
    # First line should not be the function's "signature"
    D402

# Exclude test files and specific directories from some checks
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    .eggs,
    *.egg,
    build,
    dist,
    .pytest_cache,
    htmlcov,
    coverage.xml,
    instance,
    static,
    data

# Test files can have additional ignored rules
per-file-ignores =
    tests/*.py:D,F841,F401
    test_*.py:D,F841,F401
    conftest.py:D,F401,E402
    */tests/*:D,F841,F401
    setup.py:D
    manage.py:D
    run_tests.py:D
    verify_table_structure.py:D

# Maximum complexity
max-complexity = 12

# Import order settings
import-order-style = google
application-import-names = brick_manager,services,routes,models
"""

    config_path = Path.cwd() / ".flake8"
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Created .flake8 configuration file at {config_path}")


def create_maintenance_script():
    """Create a simple maintenance script for code quality."""
    script_content = """#!/bin/bash
# Code quality maintenance script

echo "🔧 Running code quality tools..."

# Format code with black
echo "📝 Formatting code with black..."
poetry run black brick_manager/

# Sort imports with isort
echo "📦 Organizing imports with isort..."
poetry run isort --profile black brick_manager/

# Run flake8 with configuration
echo "🔍 Checking code quality with flake8..."
poetry run flake8 brick_manager/

# Run tests
echo "🧪 Running tests..."
poetry run pytest

echo "✅ Code quality check completed!"
"""

    script_path = Path.cwd() / "quality_check.sh"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make it executable
    script_path.chmod(0o755)
    
    print(f"✅ Created quality check script at {script_path}")


def update_pre_commit_config():
    """Update the pre-commit configuration to include better settings."""
    config_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]
        files: ^brick_manager/

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile, black, --line-length, "88"]
        files: ^brick_manager/

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        files: ^brick_manager/
        args: [--config=.flake8]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        files: ^brick_manager/
        args: [--ignore-missing-imports, --no-strict-optional]
        additional_dependencies: [types-requests]
"""

    config_path = Path.cwd() / ".pre-commit-config.yaml"
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print(f"✅ Updated pre-commit configuration at {config_path}")


def main():
    """Main function."""
    print("🚀 Setting up code quality tools...")
    
    create_flake8_config()
    create_maintenance_script()
    update_pre_commit_config()
    
    print("\n📋 Setup completed! You can now:")
    print("1. Run './quality_check.sh' for comprehensive code quality checks")
    print("2. Install pre-commit hooks: 'poetry run pre-commit install'")
    print("3. Run flake8 with reasonable config: 'poetry run flake8 brick_manager/'")
    print("4. The .flake8 config ignores many test-related warnings while keeping important ones")
    
    print("\n💡 The configuration focuses on:")
    print("  - Code functionality (no undefined variables)")
    print("  - Import organization")
    print("  - Critical style issues")
    print("  - Ignores test file docstring requirements")
    print("  - Allows reasonable line lengths (88 chars)")


if __name__ == "__main__":
    main()