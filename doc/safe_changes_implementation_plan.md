# Implementation Plan: Safe Changes & Local CI Pipeline

This document outlines the phased implementation plan for the "Safe Changes" initiative, focusing on establishing a local CI pipeline using Taskfile and enhancing E2E testing capabilities.

## Phase 1: Foundation & Core Tooling Setup (Taskfile & Basic Tasks)

-   [x] **1.1. Install Taskfile:** Ensure Taskfile (Go-Task) is installed or provide simple installation instructions for developers (e.g., via Homebrew, Scoop, or direct binary download). *(Installation guide created in `doc/local_ci_setup_guide.md`. Developer needs to perform manual installation.)*
-   [x] **1.2. Initialize `Taskfile.yml`:** Create the initial `Taskfile.yml` at the project root.
-   [ ] **1.3. Python Environment Task(s):**
    -   [x] Define a task to check for `venv` and create/install `requirements.txt` if missing (e.g., `task setup:py`).
    -   [ ] Define a task prefix or wrapper for Python commands to ensure they run within the `venv` (e.g., `task py:run ...`). *(Will be addressed by ensuring specific Python tasks use venv paths)*
-   [x] **1.4. Node.js Environment Task(s):**
    -   [x] Define a task to check for `node_modules` and run `npm install` if missing (e.g., `task setup:js`).
-   [x] **1.5. Linting Tasks:**
    -   [x] Define `lint:py` task: Run Ruff for Python linting (`ruff check .`).
    -   [x] Define `lint:py:types` task: Run MyPy for Python type checking (`mypy src/ tests/`).
    -   [x] Define `lint:js` task: Run ESLint for JavaScript/TypeScript linting (`npx eslint src/static/js/ tests/e2e/` - adjust paths as needed).
    -   [x] Define `lint:all` task with dependencies on `lint:py`, `lint:py:types`, and `lint:js`.
-   [x] **1.6. Python Unit & API Testing Tasks:**
    -   [x] Define `test:py:unit` task: Run Pytest for unit tests (e.g., `pytest tests/unit/`).
    -   [x] Define `test:py:api` task: Run Pytest for API/integration tests (e.g., `pytest tests/integration/`).
    -   [x] Define `test:py:cov` task: Run Pytest with coverage for all Python tests (`pytest --cov=src --cov-report=html --cov-report=term tests/unit/ tests/integration/`).
    -   [x] Define `test:py:all` task with dependencies on `test:py:unit` and `test:py:api`. *(Changed to depend on test:py:cov for default coverage)*

## Phase 2: E2E Testing Integration (Playwright)

-   [x] **2.1. Playwright Setup & Basic E2E Task:**
    -   [x] Ensure Playwright is installed (`npx playwright install`) and configured (`playwright.config.ts` if using TypeScript for tests, or equivalent for JS). *(Added @playwright/test to package.json, created playwright.config.js, created setup:e2e Taskfile task)*
    -   [x] Define `test:e2e` task: Run Playwright tests (`npx playwright test`).
    -   [x] Ensure E2E tests can target a locally running dev server. *(Configured baseURL in playwright.config.js; server start is currently manual)*
-   [x] **2.2. Comprehensive `test:all` Task:**
    -   [x] Define a master `test` or `ci:local` task that depends on `lint:all`, `test:py:all` (or `test:py:cov`), and `test:e2e`.
    -   [x] This task should be the single command developers run.
-   [x] **2.3. Playwright Trace Recording & Generation Workflow:**
    -   [x] Document the process for manual Playwright trace recording (`npx playwright open --save-trace <trace_file_name>.zip <URL>`). *(Added to doc/playwright_e2e_workflow.md)*
    -   [x] Develop and refine the AI prompt (as drafted in the project overview) for converting `trace.zip` files into Playwright test scripts. *(Draft prompt added to doc/playwright_e2e_workflow.md)*
    -   [x] Establish a convention for storing traces and their corresponding generated tests.
-   [x] **2.4. Canonical Playwright Test Examples:**
    -   [x] Manually write 2-3 high-quality Playwright E2E tests for core user flows (e.g., login, prompt creation, prompt editing).
    -   [x] These tests will serve as examples for AI-generated tests and for developers writing tests manually.
    -   [x] Ensure these tests use clear, maintainable selectors (e.g., `data-testid`, `aria-label`).

## Phase 3: Advanced Workflows & Developer Experience

-   [x] **3.1. AI-Driven Test Scaffolding for New Routes:**
    -   [x] Design a process/prompt for AI to generate basic Playwright test scaffolds when a new frontend route is added.
    -   [x] These scaffolds should assert basic page rendering and presence of key UI elements.
-   [x] **3.2. Incremental Typing (Ongoing):**
    -   [x] As part of regular development, add/improve Pydantic types and type hints in Python files when they are modified. *(This is an ongoing process. Developers should adhere to this.)*
    -   [x] Ensure `mypy` checks pass for modified files. *(Covered by `lint:py:types` task in Taskfile.yml)*
-   [x] **3.3. Developer Documentation & Onboarding:**
    -   [x] Create a `CONTRIBUTING.md` or update `README.md` with instructions on using the new local CI pipeline (Taskfile commands, testing strategies, E2E generation workflow).
-   [x] **3.4. Git Hooks (Optional Enhancement):**
    -   [x] Explore setting up pre-commit or pre-push Git hooks (e.g., using `husky` or `pre-commit`) to automatically run linting and/or a subset of tests. *(Initial exploration and potential tools documented in `doc/git_hooks_exploration.md`. Full implementation is a future step.)*

## Phase 4: Review and Iteration

-   [ ] **4.1. Gather Developer Feedback:** After initial rollout, collect feedback from the team on the usability and effectiveness of the local CI pipeline.
-   [ ] **4.2. Iterate and Refine:** Make adjustments to tasks, workflows, and documentation based on feedback and observed results.
-   [ ] **4.3. Monitor Regression Rates:** Track if the new pipeline contributes to a reduction in regressions over time.

---
*This plan is a living document and may be updated as the project progresses.* 