#!/bin/bash
"""
Install Git hooks for the Brick Manager project.
"""

set -e

echo "🔧 Installing Git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
#
# Pre-commit hook for Brick Manager
# Runs code quality checks before allowing commit
#

set -e

echo "🔍 Running pre-commit checks..."

# Run the pre-commit analysis script
if ! poetry run python scripts/pre_commit_analysis.py --no-tests; then
    echo ""
    echo "❌ Pre-commit checks failed!"
    echo "Please fix the issues above before committing."
    echo ""
    echo "To run checks manually: ./scripts/manual_precommit.sh"
    echo "To bypass this hook (not recommended): git commit --no-verify"
    exit 1
fi

echo "✅ Pre-commit checks passed!"
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

# Create commit-msg hook for conventional commits
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash
#
# Commit message hook for conventional commits
#

commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .{1,50}'

error_msg="❌ Invalid commit message format!

Commit message should follow conventional commits format:
<type>[optional scope]: <description>

Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert

Examples:
  feat: add user authentication
  fix(api): resolve database connection issue
  docs: update installation instructions
  refactor: simplify user service logic

Your commit message:
$(cat $1)"

if ! grep -qE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
EOF

chmod +x .git/hooks/commit-msg

# Create pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
#
# Pre-push hook for running tests
#

set -e

echo "🧪 Running tests before push..."

if ! poetry run pytest --tb=short -q; then
    echo ""
    echo "❌ Tests failed! Cannot push."
    echo "Please fix failing tests before pushing."
    echo ""
    echo "To bypass this hook (not recommended): git push --no-verify"
    exit 1
fi

echo "✅ All tests passed!"
EOF

chmod +x .git/hooks/pre-push

echo "✅ Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  • pre-commit: Runs code quality checks"
echo "  • commit-msg: Enforces conventional commit format"
echo "  • pre-push: Runs tests before push"
echo ""
echo "To bypass hooks (not recommended): use --no-verify flag"