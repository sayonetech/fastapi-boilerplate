#!/usr/bin/env bash
#
# This script runs a series of checks to ensure code quality and security.
# It performs formatting, linting, and vulnerability scanning.
#
# Usage:
#   bash scripts/lint.sh
#
# Dependencies:
#   - uv: For running Python tools in the project's virtual environment.
#   - ruff: For formatting and linting.
#   - pip-audit: For checking for known security vulnerabilities.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---

# Get the root directory of the Git repository
# This ensures that the script can be run from any directory within the project
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Define paths relative to the project root
SRC_PATH="$PROJECT_ROOT"

# --- Colors for Output ---
# Adds a splash of color to make the output more readable.
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_CYAN='\033[0;36m'

# --- Helper Functions ---

# Prints a formatted header for each section of the script.
# This makes it clear what part of the linting process is running.
print_header() {
    echo -e "\n${COLOR_CYAN}--- $1 ---${COLOR_RESET}"
}

# --- Main Script ---

# Navigate to the project root to ensure consistency.
cd "$PROJECT_ROOT"

# 1. Formatting with Ruff
# -----------------------
# Ruff's formatter ensures a consistent code style across the project.
# It's fast and integrates well with the linter.
print_header "Running Ruff Formatter"
uv run ruff format "$SRC_PATH"
echo -e "${COLOR_GREEN}Formatting complete.${COLOR_RESET}"

# 2. Linting with Ruff
# --------------------
# Ruff's linter checks for code errors, style issues, and automatically
# fixes many of them. This includes removing unused imports and sorting them.
print_header "Running Ruff Linter with Autofix"
uv run ruff check "$SRC_PATH" --fix
echo -e "${COLOR_GREEN}Linting and autofixing complete.${COLOR_RESET}"

# 3. Security Vulnerability Check with pip-audit
# ----------------------------------------------
# This command scans the project's dependencies for known security vulnerabilities.
# It uses the `pip-audit` tool through `uv`.
# The `--local` flag ensures it checks only local dependencies.
# The `--fix` flag attempts to automatically update vulnerable packages.
# The `--progress-spinner off` flag provides cleaner output in CI/CD environments.
print_header "Checking for Security Vulnerabilities"
uv run pip-audit --local --fix --progress-spinner off
echo -e "${COLOR_GREEN}Security check complete.${COLOR_RESET}"

# --- Final Message ---
echo -e "\n${COLOR_GREEN}✅ All checks passed successfully!${COLOR_RESET}\n"
