# Makefile for aicfg

VENV := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
PIP := $(VENV)/bin/pip

.PHONY: test setup install clean

# --- Development / Testing ---

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

# 'setup' prepares the local venv for testing
setup: $(VENV)/bin/activate
	@echo "Setting up local dev environment..."
	$(PIP) install -e .[dev] --index-url https://pypi.org/simple

# 'test' runs pytest inside the local venv
test: setup
	@echo "Running tests..."
	$(PYTEST) tests

# --- Global Installation ---

# 'install' installs the tool globally via pipx for daily use
install:
	@echo "Installing globally via pipx..."
	pipx install -e . --force --pip-args="--index-url https://pypi.org/simple"

clean:
	rm -rf build dist *.egg-info __pycache__
	rm -rf .pytest_cache
	rm -rf $(VENV)