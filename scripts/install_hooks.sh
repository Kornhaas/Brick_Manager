#!/bin/bash
# Install Git hooks for the Brick Manager project.

set -e

echo "🔧 Installing Git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

poetry run pre-commit install --install-hooks --overwrite

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

echo "✅ Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  • pre-commit: Runs Ruff linting and formatting"
echo "  • commit-msg: Enforces conventional commit format"
echo ""
echo "To bypass hooks (not recommended): use --no-verify flag"
