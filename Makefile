# Use bash for all recipes
SHELL := /bin/bash

# Variables 
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip

# Arguments 
.DEFAULT_GOAL := help

# Phony Targets 
.PHONY: run clean test help lint db-seed db-clean db-setup seed-users

# ==============================================================================
# CORE COMMANDS - For everyday development
# ==============================================================================

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
	@echo "Database Commands:"
	@echo "  make db-setup     Reset the database to a clean, seeded state. (Runs db-clean then db-seed)"
	@echo "  make db-seed   Populate the database with initial data."
	@echo "  make db-clean  Delete all book data from the database."
	@echo "  make seed-users  Populate the database with initial user data."

install: $(PIP)

$(PIP): requirements.txt
	@echo "--> Creating virtual environment and installing dependencies..."
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	## pip is idempotent. It will only install what's necessary.
	$(PIP) install -r requirements.txt
	@echo "Installation complete."

run: $(PIP)
	@echo "--> Starting Flask development server..."
	# We call python directly from the venv. No activation needed.
	$(PYTHON) -m flask --debug run

test: $(PIP)
	@echo "--> Running tests via run_tests.sh script..."
	PATH=$(VENV_DIR)/bin:$$PATH ./run_tests.sh

lint: $(PIP)
	@echo "--> Running linter..."
	PATH=$(VENV_DIR)/bin:$$PATH ./run_pylint.sh

format: $(PIP)
	@echo "--> Formatting code..."
	$(PYTHON) -m black .
	$(PYTHON) -m isort .

clean:
	@echo "--> Cleaning up local project directory..."
	rm -rf $(VENV_DIR)
	rm -rf `find . -name __pycache__`
	rm -f .coverage
	rm -rf .pytest_cache
	rm -rf htmlcov
	@echo "--> Cleanup complete."

# ==============================================================================
# DATABASE COMMANDS 
# ==============================================================================
db-setup:
	@echo ""
	@echo "⚠️  WARNING: Full Database Reset in Progress"
	@echo ""
	$(MAKE) db-clean
	$(MAKE) db-seed
	@echo "✅ Setup complete. Database has been reset and seeded."

db-seed: install
	@echo "Populating Database with books..."
	PATH=$(VENV_DIR)/bin:$$PATH PYTHONPATH=. $(PYTHON) -m scripts.create_books

db-clean: install
	@echo "--> ⚠️  Deleting all books from the database..."
	PATH=$(VENV_DIR)/bin:$$PATH PYTHONPATH=. $(PYTHON) -m scripts.delete_books


seed-users: install
	@echo "--- Seeding the database with user data ---"
	PATH=$(VENV_DIR)/bin:$$PATH PYTHONPATH=. $(PYTHON) -m scripts.seed_users
