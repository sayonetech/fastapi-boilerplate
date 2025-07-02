# Makefile for beco-mcp-server
#
# This Makefile provides a set of commands to streamline common development tasks.
# It helps in automating processes like linting, running the application, and managing dependencies.
#
# To see a list of available commands, run:
#   make help

# --- Configuration ---

# Use bash as the default shell for executing recipes.
# This provides more consistent behavior for scripts.
SHELL := /bin/bash

# --- Phony Targets ---

# Phony targets are not associated with files. They are used for commands.
# This prevents `make` from getting confused if a file with the same name as a target exists.
.PHONY: help lint run

# --- Default Target ---

# The `help` target is the default. It runs when you execute `make` without specifying a target.
# It prints a list of available commands and their descriptions.
help:
	@echo "Available commands:"
	@echo "  make help      -- Show this help message"
	@echo "  make lint      -- Run linting, formatting, and security checks"
	@echo "  make run       -- Run the FastAPI development server"

# --- Main Targets ---

# The `lint` target executes the linting script.
# This script handles formatting, static analysis, and security vulnerability checks.
lint:
	@echo "--- Running Linter and Security Checks ---"
	@bash scripts/lint.sh
	@echo "--- Linting Complete ---"

# The `run` target starts the FastAPI application in development mode.
# It uses `uvicorn` with hot-reloading enabled, so the server will restart on code changes.
run:
	@echo "--- Starting Development Server ---"
	@uvicorn main:app --reload --host 0.0.0.0 --port 8000
	@echo "--- Server Stopped ---"
