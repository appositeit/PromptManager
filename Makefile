# Makefile for Prompt Manager

HOSTNAME = $(shell hostname)
VENV_DIR = $(HOSTNAME)_venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(PYTHON) -m pytest

# Directories
SRC_DIR = src
TEST_DIR = tests
UNIT_TEST_DIR = $(TEST_DIR)/unit
INTEGRATION_API_TEST_DIR = $(TEST_DIR)/integration/api
E2E_TEST_DIR = $(TEST_DIR)/e2e
HELPER_DIR = $(TEST_DIR)/helpers

# Default target
.PHONY: default
default: help

# Help
.PHONY: help
help:
	@echo "Prompt Manager Makefile"
	@echo "-----------------------"
	@echo "Available targets:"
	@echo "  venv                - Create a Python virtual environment and install dependencies"
	@echo "  install             - Install/update dependencies from requirements.txt"
	@echo "  freeze              - Update requirements.txt with current environment"
	@echo ""
	@echo "  test                - Run all tests (unit, integration API)"
	@echo "  test-all            - Alias for 'test'"
	@echo "  test-unit           - Run unit tests"
	@echo "  test-api            - Run API integration tests (excluding websocket tool)"
	@echo "  test-websocket-integration - Run WebSocket integration tests"
	@echo "  test-integration    - Run all integration tests (API + WebSocket)"
	@echo "  test-e2e            - Run end-to-end workflow tests"
	@echo "  test-copy           - Run copy functionality tests (unit + e2e)"
	@echo "  test-copy-unit      - Run copy functionality unit tests"
	@echo "  test-copy-e2e       - Run copy functionality E2E tests"
	@echo "  test-comprehensive  - Run ALL tests (unit + integration + e2e)"
	@echo ""
	@echo "  test-cov            - Run unit+API tests with coverage report"
	@echo "  test-cov-html       - Run unit+API tests with HTML coverage report"
	@echo "  test-cov-comprehensive - Run ALL tests with comprehensive coverage report"
	@echo ""
	@echo "  run-static-server   - Run the static serving test helper server"
	@echo "  run-rename-server   - Run the rename test helper server"
	@echo "  run-api-server      - Run the basic API test helper server"
	@echo "  run-routes-server   - Run the routes test helper server"
	@echo ""
	@echo "  clean               - Remove build artifacts (preserves logs)"
	@echo "  clean-all           - Remove all artifacts including logs"
	@echo "  lint                - Run all linting checks"
	@echo "  lint-js             - Run ESLint on JavaScript files"
	@echo "  lint-js-fix         - Run ESLint with auto-fix on JavaScript files"
	@echo "  lint-cpd            - Run jscpd to detect code duplication"
	@echo ""

# Environment and Dependencies
.PHONY: venv
venv: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate: requirements.txt
	test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/$(PIP) install --upgrade pip
	$(VENV_DIR)/bin/$(PIP) install -r requirements.txt
	touch $(VENV_DIR)/bin/activate

.PHONY: install
install:
	$(VENV_DIR)/bin/$(PIP) install -r requirements.txt

.PHONY: freeze
freeze:
	$(VENV_DIR)/bin/$(PIP) freeze > requirements.txt

# New target to ensure server is running
.PHONY: ensure-server-running
ensure-server-running:
	@echo "Ensuring server is (re)started and alive..."
	bash bin/restart_prompt_manager.sh

# Test runners
.PHONY: test test-all
test test-all: test-unit test-api
	@echo "All main tests completed."

.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	$(PYTEST) $(UNIT_TEST_DIR)

.PHONY: test-api
test-api: ensure-server-running
	@echo "Running API integration tests..."
	$(PYTEST) $(INTEGRATION_API_TEST_DIR) -k "not test_websocket_connection_tool"

.PHONY: test-integration
test-integration: test-api test-websocket-integration # Add other integration test categories
	@echo "Running all integration tests..."

.PHONY: test-websocket-integration  
test-websocket-integration: ensure-server-running
	@echo "Running WebSocket integration tests..."
	$(PYTEST) tests/integration/test_websocket_comprehensive.py -k "not test_websocket_connection_tool"

.PHONY: test-e2e
test-e2e: ensure-server-running
	@echo "Running E2E tests..."
	$(PYTEST) $(E2E_TEST_DIR)

.PHONY: test-copy
test-copy: ensure-server-running
	@echo "Running copy functionality tests..."
	$(PYTEST) $(UNIT_TEST_DIR)/test_copy_functionality_js.py $(E2E_TEST_DIR)/test_copy_functionality.py

.PHONY: test-copy-unit
test-copy-unit:
	@echo "Running copy functionality unit tests..."
	$(PYTEST) $(UNIT_TEST_DIR)/test_copy_functionality_js.py

.PHONY: test-copy-e2e
test-copy-e2e: ensure-server-running
	@echo "Running copy functionality E2E tests..."
	$(PYTEST) $(E2E_TEST_DIR)/test_copy_functionality.py

.PHONY: test-copy-bug-fix
test-copy-bug-fix: ensure-server-running
	@echo "Running copy bug fix validation tests..."
	$(PYTEST) $(E2E_TEST_DIR)/test_copy_bug_fix.py

.PHONY: test-comprehensive
test-comprehensive: test-unit test-integration test-e2e
	@echo "Running comprehensive test suite..."

# Coverage
.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing $(UNIT_TEST_DIR) $(INTEGRATION_API_TEST_DIR) tests/integration/test_websocket_comprehensive.py -k "not test_websocket_connection_tool"

.PHONY: test-cov-html
test-cov-html:
	@echo "Running tests with HTML coverage report..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=html:artifacts/coverage/basic $(UNIT_TEST_DIR) $(INTEGRATION_API_TEST_DIR) tests/integration/test_websocket_comprehensive.py -k "not test_websocket_connection_tool"
	@echo "HTML coverage report generated in artifacts/coverage/basic directory."

.PHONY: test-cov-comprehensive
test-cov-comprehensive: ensure-server-running
	@echo "Running comprehensive tests with coverage..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html:artifacts/coverage/comprehensive $(UNIT_TEST_DIR) $(INTEGRATION_API_TEST_DIR) tests/integration/test_websocket_comprehensive.py $(E2E_TEST_DIR) -k "not test_websocket_connection_tool"
	@echo "Comprehensive coverage report generated in artifacts/coverage/comprehensive directory."

.PHONY: test-cov-true
test-cov-true: ensure-server-running
	@echo "Running TRUE comprehensive coverage (including API route execution)..."
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html:artifacts/coverage/true --cov-config=.coveragerc-true $(UNIT_TEST_DIR) $(INTEGRATION_API_TEST_DIR) tests/integration/test_websocket_comprehensive.py -k "not test_websocket_connection_tool"
	@echo "True coverage report (unit + integration tests) generated in artifacts/coverage/true directory."

# Helper Server Runners
.PHONY: run-static-server
run-static-server:
	@echo "Starting static serving test helper server..."
	$(PYTHON) $(HELPER_DIR)/static_serving_test_server.py

.PHONY: run-rename-server
run-rename-server:
	@echo "Starting rename test helper server..."
	$(PYTHON) $(HELPER_DIR)/rename_test_server.py

.PHONY: run-api-server
run-api-server:
	@echo "Starting basic API test helper server..."
	$(PYTHON) $(HELPER_DIR)/basic_api_test_server.py

.PHONY: run-routes-server
run-routes-server:
	@echo "Starting routes test helper server..."
	$(PYTHON) $(HELPER_DIR)/routes_test_server.py

# Clean
.PHONY: clean
clean:
	@echo "Cleaning up..."
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf artifacts/coverage/* artifacts/reports/* artifacts/temp/*
	rm -rf cov_html cov_html_* htmlcov
	rm -f .coverage
	@echo "All artifacts cleaned (logs preserved)."

.PHONY: clean-all
clean-all: clean
	@echo "Cleaning logs as well..."
	rm -rf artifacts/logs/*
	@echo "All artifacts including logs cleaned."

# Root directory cleanliness check
.PHONY: check-root-clean
check-root-clean:
	@echo "Checking root directory cleanliness..."
	@if find . -maxdepth 1 -type f \( -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.md" \) ! \( -name "README.md" -o -name "CONTRIBUTING.md" -o -name "eslint.config.js" -o -name ".eslintrc.js" -o -name "api_docs_template.html" -o -name "debug_routes.py" \) | grep -q .; then \
		echo "❌ ERROR: Inappropriate files found in root directory:"; \
		find . -maxdepth 1 -type f \( -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.md" \) ! \( -name "README.md" -o -name "CONTRIBUTING.md" -o -name "eslint.config.js" -o -name ".eslintrc.js" -o -name "api_docs_template.html" -o -name "debug_routes.py" \); \
		echo "🚫 Move these files to appropriate subdirectories!"; \
		exit 1; \
	else \
		echo "✅ Root directory is clean"; \
	fi

# Lint (includes root directory check)
.PHONY: lint
lint: check-root-clean lint-js
	@echo "Linting completed successfully."
	@echo "Run 'make lint-cpd' to check for code duplication."

# JavaScript Linting  
.PHONY: lint-js
lint-js:
	@echo "Running ESLint on JavaScript files..."
	npx eslint src/static/js/

.PHONY: lint-js-fix
lint-js-fix:
	@echo "Running ESLint with auto-fix on JavaScript files..."
	npx eslint src/static/js/ --fix

# Code Duplication Check
.PHONY: lint-cpd
lint-cpd:
	@echo "Running jscpd to detect code duplication (generating HTML report in artifacts/reports/jscpd and console output)..."
	npx jscpd --reporters=html,console --output=./artifacts/reports/jscpd --ignore "**/.venv/**,**/venv/**,**/node_modules/**,**/.mypy_cache/**,**/.pytest_cache/**,**/.ruff_cache/**,**/archive/**,**/*.lock,**/data/**,**/artifacts/**,**/dist/**,**/build/**,**/tests/**" .
