# Makefile for aicfg

PIPX_VENV_BIN := $(HOME)/.local/share/pipx/venvs/aicfg/bin
PYTEST := $(PIPX_VENV_BIN)/pytest

.PHONY: test install install-dev clean

install:
	@echo "Installing aicfg in editable mode via pipx..."
	pipx install -e . --force

install-dev: install
	@echo "Injecting development dependencies (pytest)..."
	pipx inject aicfg pytest

test:
	@if [ ! -f "$(PYTEST)" ]; then \
		echo "pytest not found in pipx venv. Running install-dev..."; \
		$(MAKE) install-dev; \
	fi
	$(PYTEST) tests/integration

clean:
	rm -rf build dist *.egg-info __pycache__
	rm -rf .pytest_cache
