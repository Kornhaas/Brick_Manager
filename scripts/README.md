# Pre-Commit Analysis and Code Quality Setup

This directory contains scripts and configuration for automated code quality checks and pre-commit analysis.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
poetry install
```

### 2. Install Git Hooks (Recommended)
```bash
./scripts/install_hooks.sh
```

### 3. Run Manual Analysis
```bash
./scripts/manual_precommit.sh
```

## 📁 Files Overview

### Core Scripts
- **`pre_commit_analysis.py`** - Main analysis script with auto-fixing capabilities
- **`manual_precommit.sh`** - Bash wrapper for manual execution
- **`install_hooks.sh`** - Installs Git hooks for automated checking

### Custom Checkers
- **`security_check.py`** - Security-focused code analysis
- **`custom_checks.py`** - Project-specific code quality checks

### Configuration
- **`.pre-commit-config.yaml`** - Pre-commit framework configuration
- **`pyproject.toml`** - Tool configurations (Black, isort, mypy, etc.)

## 🔧 What Gets Checked and Fixed

### Automatic Fixes Applied:
- ✅ **Code Formatting** (Black)
- ✅ **Import Sorting** (isort)
- ✅ **Trailing Whitespace** removal
- ✅ **Missing Docstrings** (basic placeholders added)
- ✅ **Line Length** issues (simple cases)
- ✅ **File Endings** (ensure newline at EOF)

### Quality Checks:
- 🔍 **Code Style** (flake8)
- 🔍 **Code Quality** (pylint)
- 🔍 **Security Issues** (bandit + custom checks)
- 🔍 **Type Hints** (mypy)
- 🔍 **Custom Rules** (function complexity, docstrings, etc.)

### Testing:
- 🧪 **Unit Tests** (pytest)
- 📊 **Coverage Reports**

## 🎯 Usage Examples

### Run Full Analysis with Auto-Fix
```bash
poetry run python scripts/pre_commit_analysis.py
```

### Run Analysis Without Auto-Fix
```bash
poetry run python scripts/pre_commit_analysis.py --no-fix
```

### Run Analysis Without Tests (Faster)
```bash
poetry run python scripts/pre_commit_analysis.py --no-tests
```

### Run Individual Tools
```bash
# Format code
poetry run black brick_manager/

# Sort imports
poetry run isort brick_manager/

# Run linting
poetry run flake8 brick_manager/
poetry run pylint brick_manager/

# Security check
poetry run bandit -r brick_manager/

# Type checking
poetry run mypy brick_manager/

# Run tests
poetry run pytest
```

## 🔗 Git Hooks

After running `./scripts/install_hooks.sh`, three hooks are installed:

### Pre-Commit Hook
- Runs before each commit
- Performs code formatting and quality checks
- Prevents commits with serious issues
- Can be bypassed with `git commit --no-verify` (not recommended)

### Commit Message Hook
- Enforces conventional commit format
- Examples of valid messages:
  - `feat: add user authentication`
  - `fix(api): resolve database connection issue`
  - `docs: update installation instructions`

### Pre-Push Hook
- Runs full test suite before push
- Prevents pushing code that breaks tests
- Can be bypassed with `git push --no-verify` (not recommended)

## 📊 Understanding the Output

### Success Indicators
- ✅ Green checkmarks indicate passed checks
- 🔧 Wrench icons show auto-fixes applied

### Warning Indicators
- ⚠️ Yellow warnings for non-blocking issues
- These won't prevent commits but should be addressed

### Error Indicators
- ❌ Red errors for blocking issues
- Must be fixed before committing

### Example Output
```
🚀 Starting pre-commit analysis...
🔧 Formatting code with Black...
✅ Black formatting applied
📦 Sorting imports with isort...
✅ No import sorting needed
🔍 Running flake8 linting...
✅ flake8 passed
🔍 Running pylint analysis...
✅ pylint passed with score: 8.5/10
🔒 Running Bandit security analysis...
✅ Bandit security check passed
🧪 Running tests...
✅ All tests passed

==========================================
📊 PRE-COMMIT ANALYSIS REPORT
==========================================

✅ FIXES APPLIED:
  • Black: Auto-formatted Python files
  • Fixed common issues in missing_parts.py

🎉 All checks passed! Code is ready for commit.
==========================================
```

## ⚙️ Configuration

### Tool Configurations in `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true

[tool.bandit]
exclude_dirs = ["tests", "migrations"]
```

### Customizing Checks

Edit the configuration files to adjust:
- Line length limits
- Excluded directories
- Specific rule enablement/disablement
- Test coverage thresholds

## 🚫 Bypassing Checks

While not recommended, you can bypass checks:

```bash
# Skip pre-commit hook
git commit --no-verify

# Skip pre-push hook
git push --no-verify

# Run only specific checks
poetry run python scripts/pre_commit_analysis.py --no-tests
```

## 🔧 Troubleshooting

### Common Issues

1. **Poetry not found**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Permission denied on scripts**
   ```bash
   chmod +x scripts/*.sh scripts/*.py
   ```

3. **Tests failing**
   ```bash
   # Run tests with more verbose output
   poetry run pytest -v --tb=long
   ```

4. **Pylint score too low**
   - Address the specific issues shown in the output
   - Consider adjusting pylint configuration if needed

### Getting Help

The analysis script provides detailed output about what failed and how to fix it. Look for:
- Specific line numbers for issues
- Suggested fixes
- Command examples for manual resolution

## 🎯 Best Practices

1. **Run checks frequently** during development
2. **Fix issues incrementally** rather than accumulating them
3. **Read the output** to understand what each tool is checking
4. **Customize configurations** to match your project needs
5. **Don't bypass hooks** unless absolutely necessary
6. **Keep dependencies updated** regularly

## 📈 Integration with CI/CD

This setup is designed to work well with CI/CD pipelines. The same scripts can be run in:
- GitHub Actions
- GitLab CI
- Jenkins
- Any other CI system

Example GitHub Action:
```yaml
- name: Run pre-commit analysis
  run: |
    poetry install
    poetry run python scripts/pre_commit_analysis.py
```