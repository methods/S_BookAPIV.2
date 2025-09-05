# Use bash for all recipes
SHELL := /bin/bash

# Variables 
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip
# A reusable prefix for running our python scripts as modules from the project root.
RUN_SCRIPT = PATH=$(VENV_DIR)/bin:$$PATH PYTHONPATH=. $(PYTHON) -m


# Arguments 
.DEFAULT_GOAL := help

# Phony Targets 
.PHONY: run clean clean-db test help lint db-seed db-clean db-setup seed-users setup books reservations

# ==============================================================================
# CORE COMMANDS - For everyday development
# ==============================================================================

help: ## Show help
	@echo ""
	@echo "Usage:"
	@echo "  make install      Install project dependencies into a virtual environment."
	@echo "  make run          Run the Flask development server."
	@echo "  make test         Run unit tests with pytest and generate a coverage report."
	@echo "  make lint         Run the pylint linter on the source code."
	@echo "  make format       Auto-format the code using black and isort."
	@echo "  make clean        Remove virtual environment and temporary files."
	@echo ""
	@echo "Database Commands:"
	@echo "  make setup        Reset and populate with books and reservations."
	@echo "  make clean-db     Delete all books AND reservations from the database."
	@echo "  make books        Populate the database with books. (Alias: db-seed)"
	@echo "  make reservations Populate the database with reservations."
	@echo "  make seed-users   Populate the database with initial user data."
	@echo "  make db-clean     (DEPRECATED) Use 'make clean-db' instead. Deletes only books."
	@echo "  make db-seed      (DEPRECATED) Use 'make books' instead."
	@echo "  make db-setup     (DEPRECATED) Use 'make setup' instead."

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

clean: ## Remove virtual environment and temporary files.
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

setup: clean-db books reservations ## Reset the database and populate with all data.
	@echo ""
	@echo "✅ Full setup complete. Database has been reset and fully seeded."

clean-db: install ## Delete all reservations and books from the database.
	@echo "--> 🧹 Deleting all reservations and books from the database..."
	$(RUN_SCRIPT) scripts.delete_reservations
	$(RUN_SCRIPT) scripts.delete_books

books: install ## Populate the database with books.
	@echo "--> 📚 Populating database with books..."
	$(RUN_SCRIPT) scripts.create_books

reservations: install ## Populate the database with reservations.
	@echo "--> 🎟️  Populating database with reservations..."
	$(RUN_SCRIPT) scripts.seed_reservations

# --- Deprecated / Aliased Targets for backwards compatibility ---
db-setup:
	@echo ""
	@echo "⚠️  DEPRECATION WARNING: 'make db-setup' is deprecated. Please use 'make setup'."
	@echo ""
	$(MAKE) db-clean
	$(MAKE) db-seed
	@echo "✅ Old setup complete. Database has been reset and seeded with books only."

db-seed: books ## DEPRECATED: Alias for 'make books'
	@echo "--> NOTE: 'make db-seed' is an alias for 'make books'."

db-clean: install ## DEPRECATED: Use 'make clean-db'
	@echo "--> ⚠️  DEPRECATION WARNING: 'make db-clean' only deletes books. Use 'make clean-db' to delete all data."
	$(RUN_SCRIPT) scripts.delete_books

seed-users: install
	@echo "--- Seeding the database with user data ---"
	$(RUN_SCRIPT) scripts.seed_users