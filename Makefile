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

# Run all examples
.PHONY: examples
examples: example-env
	@echo "=== Running all examples ==="
	@echo "\n[1/5] Running email analysis example..."
	@$(PYTHON) examples/01_email_analysis.py || echo "Skipping..."
	@echo "\n[2/5] Running IMAP email processor example..."
	@$(PYTHON) examples/02_imap_email_processor.py || echo "Skipping..."
	@echo "\n[3/5] Running email organizer example..."
	@$(PYTHON) examples/03_email_organizer.py || echo "Skipping..."
	@echo "\n[4/5] Running email summarizer example..."
	@$(PYTHON) examples/04_email_summarizer.py || echo "Skipping..."
	@echo "\n[5/5] Running command line IMAP example..."
	@$(PYTHON) examples/05_command_line_imap.py --limit 2 || echo "Skipping..."
	@echo "\n=== All examples completed ==="

# Run command line IMAP example
.PHONY: example-cmd
# Example: make example-cmd IMAP_SERVER=imap.example.com IMAP_EMAIL=user@example.com IMAP_PASSWORD=pass
example-cmd: example-env
	@echo "Running command line IMAP example..."
	@$(PYTHON) examples/05_command_line_imap.py \
		--imap-server $(or $(IMAP_SERVER),$(shell grep -E '^IMAP_SERVER=' .env | cut -d= -f2-)) \
		--email $(or $(IMAP_EMAIL),$(shell grep -E '^IMAP_EMAIL=' .env | cut -d= -f2-)) \
		--password $(or $(IMAP_PASSWORD),$(shell grep -E '^IMAP_PASSWORD=' .env | cut -d= -f2-)) \
		--limit 5

# Run with Docker Compose
.PHONY: docker-up
docker-up:
	@if [ ! -f docker-compose.yml ]; then \
		cp examples/docker-compose.example.yml docker-compose.yml; \
		echo "Created docker-compose.yml from example. Please edit it with your settings."; \
		exit 1; \
	fi
	@if ! grep -q 'IMAP_SERVER=' docker-compose.yml || ! grep -q 'IMAP_EMAIL=' docker-compose.yml || ! grep -q 'IMAP_PASSWORD=' docker-compose.yml; then \
		echo "Error: Please configure IMAP settings in docker-compose.yml"; \
		exit 1; \
	fi
	docker-compose up -d
	@echo "\nDocker containers started. Check logs with: make docker-logs"

# View Docker logs
.PHONY: docker-logs
docker-logs:
	docker-compose logs -f

# Stop Docker containers
.PHONY: docker-down
docker-down:
	docker-compose down

# Create .env from example if it doesn't exist
example-env:
	@if [ ! -f .env ]; then \
		cp examples/.env.example .env; \
		echo "Created .env from example. Please edit it with your settings."; \
		exit 1; \
	fi
	@if ! grep -q 'IMAP_SERVER=' .env || ! grep -q 'IMAP_EMAIL=' .env || ! grep -q 'IMAP_PASSWORD=' .env; then \
		echo "Error: Please configure IMAP settings in .env"; \
		exit 1; \
	fi

# Add examples to help
help-examples:
	@echo "Available dun command examples:"
	@echo "  make examples            - Run all examples (requires .env configuration)"
	@echo "  make example-cmd         - Run command line IMAP example (requires IMAP_* env vars)"
	@echo "  make docker-up           - Start Docker containers (requires docker-compose.yml)"
	@echo "  make docker-logs        - View Docker container logs"
	@echo "  make docker-down        - Stop Docker containers"

# Add examples to help
help: help-examples


# Run full test suite
.PHONY: test-all
test-all: lint type-check test
	echo "All tests passed!"
