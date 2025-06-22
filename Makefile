# Project Makefile for emllm (Large Language Model Email Message Language)

# Project name
PROJECT_NAME = emllm

# Poetry environment
POETRY := poetry

# Python paths
PYTHON := python3
PYTHON_SRC := src/$(PROJECT_NAME)

.PHONY: install test lint clean build publish docs start-server test-message test-api test-cli

# Install dependencies and package
install:
	$(POETRY) install

# Run all tests
.PHONY: test
test:
	$(PYTHON) -m pytest tests/ --cov=$(PYTHON_SRC) --cov-report=term-missing

# Run API tests
.PHONY: test-api
test-api:
	$(PYTHON) -m pytest tests/test_api.py

# Run CLI tests
.PHONY: test-cli
test-cli:
	$(PYTHON) -m pytest tests/test_cli.py

# Run validator tests
.PHONY: test-validator
test-validator:
	$(PYTHON) -m pytest tests/test_validator.py

# Run linters
.PHONY: lint
lint:
	$(PYTHON) -m black .
	$(PYTHON) -m isort .
	$(PYTHON) -m flake8 .

# Run type checking
.PHONY: type-check
type-check:
	$(PYTHON) -m mypy .

# Clean up
.PHONY: clean
clean:
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Build package
.PHONY: build
build:
	$(POETRY) version patch
	$(POETRY) build

# Publish package to PyPI
.PHONY: publish
publish: build
	$(POETRY) publish --no-interaction

# Generate documentation
.PHONY: docs
docs:
	$(PYTHON) -m pdoc --html --output-dir docs .

# Clean up
.PHONY: clean
clean:
	$(POETRY) env remove
	rm -rf .mypy_cache/ .pytest_cache/ .coverage/ .coverage.* coverage.xml htmlcov/ .cache/ .tox/ .venv/ .eggs/ *.egg-info/ dist/ build/ docs/

# Start REST server
.PHONY: start-server
start-server:
	$(PYTHON) -m emllm.cli rest --host 0.0.0.0 --port 8000

# Test message parsing
.PHONY: test-message
test-message:
	$(PYTHON) -m emllm.cli parse "From: test@example.com\nTo: recipient@example.com\nSubject: Test\n\nHello World"

# Run dun with example email processing
.PHONY: example-email-process
example-email-process:
	$(PYTHON) run_dun.py

# Example: Process emails from IMAP and organize by date
.PHONY: example-imap-process
example-imap-process:
	@echo "Processing emails from IMAP and organizing by date..."
	$(PYTHON) -c "from dun.processor_engine import ProcessorEngine; from dun.llm_analyzer import LLMAnalyzer; \
	llm = LLMAnalyzer(base_url='http://localhost:11434', model='mistral:7b'); \
	engine = ProcessorEngine(llm); \
	engine.process_natural_request('Pobierz wiadomości email z IMAP i posortuj je w folderach według daty (rok.miesiąc)')"

# Example: Analyze email content using LLM
.PHONY: example-analyze-email
example-analyze-email:
	@echo "Analyzing email content using LLM..."
	$(PYTHON) -c "from dun.llm_analyzer import LLMAnalyzer; \
	llm = LLMAnalyzer(base_url='http://localhost:11434', model='mistral:7b'); \
	result = llm.analyze('Przeanalizuj tę wiadomość i wyodrębnij najważniejsze informacje: \n\nWitaj, chciałbym umówić się na spotkanie w przyszłym tygodniu. Proszę o potwierdzenie dostępności. Z poważaniem, Jan Kowalski'); \
	print('Analysis result:', result)"

# Example: Run with custom request from command line
.PHONY: example-custom-request
example-custom-request:
	@echo "Running custom request..."
	@read -p "Enter your request: " request; \
	$(PYTHON) -c "from dun.processor_engine import ProcessorEngine; from dun.llm_analyzer import LLMAnalyzer; \
	llm = LLMAnalyzer(base_url='http://localhost:11434', model='mistral:7b'); \
	engine = ProcessorEngine(llm); \
	print('Processing request:', '$$request'); \
	result = engine.process_natural_request('$$request'); \
	print('\nResult:', result)"

# List all available examples
.PHONY: examples
help-examples:
	@echo "Available dun command examples:"
	@echo "  make example-email-process    - Run default email processing"
	@echo "  make example-imap-process    - Process emails from IMAP and organize by date"
	@echo "  make example-analyze-email   - Analyze email content using LLM"
	@echo "  make example-custom-request  - Run with custom request (interactive)"

# Add examples to help
help: help-examples


# Run full test suite
.PHONY: test-all
test-all: lint type-check test
	echo "All tests passed!"
