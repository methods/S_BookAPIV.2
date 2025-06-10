.DEFAULT_GOAL := help
.PHONY: run clean test help lint

# Variables 
VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip


run: $(VENV_DIR)/bin/activate
	$(PYTHON) -m flask --debug run

test: $(VENV_DIR)/bin/activate
	# Prepend virtualenv bin to PATH to use its Python and tools
	PATH=$(VENV_DIR)/bin:$$PATH ./run_tests.sh

lint: $(VENV_DIR)/bin/activate
	PATH=$(VENV_DIR)/bin:$$PATH ./run_pylint.sh

help:
	@echo "Makefile commands:"
	@echo "  make run     - Run Flask app"
	@echo "  make test    - Run tests and generates a coverage report."
	@echo "  make lint    - Runs the Pylint linter."
	@echo "  make clean   - Removes the virtual environment and cache files."
	@echo "  make help    - Shows this help message."

venv/bin/activate: requirements.txt
	python3 -m venv $(VENV_DIR)
	${PIP} install -r requirements.txt || true
	$(PIP) list --format=freeze | diff - requirements.txt || $(PIP) install -r requirements.txt

clean:
	rm -rf __pycache__
	rm -rf $(VENV_DIR)
	@echo "Cleaned up the project."