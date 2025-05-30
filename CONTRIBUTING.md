# Contributing to Prompt Manager

First off, thank you for considering contributing to Prompt Manager! Your help is appreciated.

This document provides guidelines for contributing to the project, including how to set up your development environment, run tests, and follow our development workflows.

## 1. Getting Started & Setup

### 1.1. Prerequisites

Ensure you have the following installed on your system:
-   Python (version 3.10+ recommended)
-   Node.js (version 18.x or LTS recommended, includes npm)
-   Git

### 1.2. Initial Project Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd prompt_manager
    ```

2.  **Install Taskfile (Go-Task):**
    Taskfile is our command runner for managing development tasks. Please follow the installation instructions in our [Local CI Setup Guide](./doc/local_ci_setup_guide.md).
    After installation, verify with `task --version`.

3.  **Setup Python Environment & Dependencies:**
    This command will create a Python virtual environment (`venv/`) if it doesn't exist and install all Python dependencies from `requirements.txt`.
    ```bash
    task setup:py
    ```

4.  **Setup Node.js Dependencies:**
    This command will install Node.js dependencies specified in `package.json` into the `node_modules/` directory.
    ```bash
    task setup:js
    ```

5.  **Install Playwright Browser Drivers:**
    For End-to-End (E2E) testing, we use Playwright, which requires browser drivers.
    ```bash
    task setup:e2e
    ```

## 2. Development Workflow

### 2.1. Running the Application

To run the main FastAPI application locally, use the provided scripts:

```bash
./bin/start_prompt_manager.sh
# Or, to restart if already running
./bin/restart_prompt_manager.sh
```

This will start the server and make it available at http://localhost:8081.

(You can also use `make start` or `task start` if your workflow supports it.)

### 2.2. Running Linters & Type Checks

We use Ruff for Python linting and MyPy for type checking. ESLint is used for JavaScript.

-   **Lint Python code:**
    ```bash
    task lint:py
    ```
-   **Type check Python code:**
    ```bash
    task lint:py:types
    ```
-   **Lint JavaScript code:**
    ```bash
    task lint:js
    ```
-   **Run all linters:**
    ```bash
    task lint:all
    ```

It's recommended to run `task lint:all` before committing changes.

### 2.3. Running Tests

We have unit, API/integration, and End-to-End (E2E) tests.

-   **Run Python unit tests:**
    ```bash
    task test:py:unit
    ```
-   **Run Python API/integration tests:**
    ```bash
    task test:py:api
    ```
-   **Run all Python tests with coverage:**
    ```bash
    task test:py:cov 
    # or use the alias
    task test:py:all
    ```
    Coverage reports are generated in `htmlcov/` and printed to the terminal.

-   **Run End-to-End (E2E) Playwright tests:**
    Ensure the development server is running (see section 2.1).
    ```bash
    task test:e2e
    ```

### 2.4. Full Local CI Check

To run all linters and all tests (Python with coverage, and E2E), use the main local CI task:

```bash
task ci:local
```

This is the command you should run before pushing changes to ensure everything is passing.

### 2.5. End-to-End Testing Workflow (Playwright)

For details on recording Playwright traces, using AI for test generation, and other E2E best practices, please refer to our [Playwright E2E Workflow Guide](./doc/playwright_e2e_workflow.md).

### 2.6. Incremental Typing (Python)

As a general practice, when you modify a Python file, please add or improve Pydantic types and standard type hints. Ensure `task lint:py:types` (or `task lint:all` / `task ci:local`) passes after your changes.

## 3. Submitting Changes

-   Ensure `task ci:local` passes before committing.
-   Follow standard Git commit message conventions.
-   Push your changes to a feature branch and open a Pull Request (PR) against the main development branch (e.g., `main` or `develop`).
-   Ensure your PR description clearly describes the changes and any relevant context.

## 4. Code Style

-   Python: Follow PEP 8. Ruff (`task lint:py`) will help enforce this.
-   JavaScript/TypeScript: Follow the ESLint configuration (`task lint:js`).

## 5. Questions?

If you have questions, feel free to ask existing contributors or open an issue on the project's issue tracker.

---
*This document is a living guide and may be updated as project practices evolve.* 