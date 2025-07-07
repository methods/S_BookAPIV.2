# Use bash for all recipes
SHELL := /bin/bash

# Variables 
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip

# Arguments 
.DEFAULT_GOAL := help

# Phony Targets 
.PHONY: run clean test help lint

# CORE COMMANDS

help: ## Show help
	@echo ""
	@echo "Usage:"
	@echo "  make install   Install project dependencies into a virtual environment."
	@echo "  make run       Run the Flask development server."
	@echo "  make test      Run unit tests with pytest and generate a coverage report."
	@echo "  make lint      Run the pylint linter on the source code."
	@echo "  make format    Auto-format the code using black and isort."
	@echo "  make clean     Remove virtual environment and temporary files."
	@echo ""

install: $(PIP)

$(PIP): requirements.txt
	@echo "Creating virtual environment and installing dependencies..."
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	## pip is idempotent. It will only install what's necessary.
	$(PIP) install -r requirements.txt
	@echo "Installation complete."

run: $(PIP)
	@echo "Starting Flask development server..."
	# We call python directly from the venv. No activation needed.
	$(PYTHON) -m flask --debug run

test: $(PIP)
	@echo "Running tests via run_tests.sh script..."
	# The '$$' is needed to escape the '$' for make.
	PATH=$(VENV_DIR)/bin:$$PATH ./run_tests.sh

lint: $(PIP)
	@echo "Running linter..."
	PATH=$(VENV_DIR)/bin:$$PATH ./run_pylint.sh

format: $(PIP)
	@echo "Formatting code..."
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

venv/bin/activate: requirements.txt
	python3 -m venv $(VENV_DIR)
	${PIP} install -r requirements.txt || true
	$(PIP) list --format=freeze | diff - requirements.txt || $(PIP) install -r requirements.txt

clean: ## Clean up pyc files, caches, and venv
	rm -rf __pycache__
	rm -rf $(VENV_DIR)
	@echo "Cleaned up the project."