#!/usr/bin/env bash
#
# This script runs Bandit security checks to identify common security issues
# in Python code, such as hardcoded passwords, SQL injection vulnerabilities,
# and other security anti-patterns.
#
# Usage:
#   bash scripts/bandit.sh
#
# Dependencies:
#   - uv: For running Python tools in the project's virtual environment.
#   - bandit: For security vulnerability scanning.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---

# Get the root directory of the Git repository
# This ensures that the script can be run from any directory within the project
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Define paths relative to the project root
SRC_PATH="$PROJECT_ROOT/src"

# --- Colors for Output ---
# Adds a splash of color to make the output more readable.
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_CYAN='\033[0;36m'
COLOR_RED='\033[0;31m'

# --- Helper Functions ---

# Prints a formatted header for each section of the script.
# This makes it clear what part of the security check is running.
print_header() {
    echo -e "\n${COLOR_CYAN}--- $1 ---${COLOR_RESET}"
}

# --- Main Script ---

# Navigate to the project root to ensure consistency.
cd "$PROJECT_ROOT"

# 1. Security Check with Bandit
# -----------------------------
# Bandit scans Python code for common security issues and anti-patterns.
# It checks for things like hardcoded passwords, SQL injection vulnerabilities,
# use of dangerous functions, and other security concerns.
# The configuration is read from pyproject.toml [tool.bandit] section.
print_header "Running Bandit Security Check"
echo "Scanning for security vulnerabilities in Python code..."

# Run Bandit with configuration from pyproject.toml
if uv run bandit -r "$SRC_PATH" -c pyproject.toml; then
    echo -e "${COLOR_GREEN}Security check passed. No critical issues found.${COLOR_RESET}"
else
    echo -e "${COLOR_YELLOW}⚠️  Security issues found. Please review the output above.${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}   Some issues may be false positives or acceptable for your use case.${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}   You can skip specific tests by adding them to the 'skips' list in pyproject.toml.${COLOR_RESET}"
    exit 1
fi

# --- Final Message ---
echo -e "\n${COLOR_GREEN}✅ Security check complete!${COLOR_RESET}\n"
