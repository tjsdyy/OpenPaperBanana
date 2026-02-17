#!/bin/bash
# Pre-publish security check script
# Run this before pushing to GitHub to ensure no sensitive data is exposed

set -e

echo "🔍 Checking for sensitive information..."

# Check if .env is tracked
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "❌ ERROR: .env file is tracked by git!"
    echo "   Run: git rm --cached .env"
    exit 1
fi

# Check for API keys in tracked files
echo "Checking for API keys in tracked files..."
GOOGLE_KEY_PATTERN="AIzaSy[A-Za-z0-9_-]{33}"
if git grep -E "$GOOGLE_KEY_PATTERN" -- ':(exclude).env' ':(exclude).env.example' ':(exclude)scripts/'; then
    echo "❌ ERROR: Found Google API key in tracked files!"
    exit 1
fi

GENERIC_KEY_PATTERN="sk-[A-Za-z0-9]{48}"
if git grep -E "$GENERIC_KEY_PATTERN" -- ':(exclude).env' ':(exclude).env.example' ':(exclude)scripts/'; then
    echo "❌ ERROR: Found API key pattern in tracked files!"
    exit 1
fi

# Check for hardcoded domains (excluding documentation)
echo "Checking for hardcoded private domains..."
PRIVATE_DOMAINS=$(git grep -i "apicore\.ai\|kie\.ai" -- ':(exclude)*.md' ':(exclude).env' ':(exclude).env.example' ':(exclude)scripts/' || true)
if [ -n "$PRIVATE_DOMAINS" ]; then
    echo "⚠️  WARNING: Found references to private domains:"
    echo "$PRIVATE_DOMAINS"
    echo "   Please review if these should be configurable."
fi

# Verify .env.example exists
if [ ! -f .env.example ]; then
    echo "❌ ERROR: .env.example file is missing!"
    exit 1
fi

# Check if .env.example has placeholder values
if grep -q "your_.*_api_key_here" .env.example; then
    echo "✅ .env.example has placeholder values"
else
    echo "⚠️  WARNING: .env.example might contain real API keys!"
fi

echo ""
echo "✅ Security check passed!"
echo ""
echo "📋 Pre-publish checklist:"
echo "  [ ] .env is in .gitignore and not tracked"
echo "  [ ] .env.example has placeholder values only"
echo "  [ ] No API keys in source code"
echo "  [ ] No private domains hardcoded (or documented as examples)"
echo "  [ ] README.md updated with setup instructions"
echo ""
echo "Ready to publish! 🚀"
