# feature UI Refinement

## Problem

We are building a Python FastAPI/Starlette + JS app called **Prompt Manager** for managing AI prompts. Development velocity has been slowed by frequent regressions when adding new features, even with decent unit and API test coverage.

End-to-end (E2E) tests written by AI currently require too much hand-holding. We'd like to increase the **autonomy of AI-generated E2E tests** and reduce regressions via a structured local CI pipeline.

## Goals
- Automate testing (unit, API, and E2E) locally.
- Reduce human effort during feature rollout.
- Allow AI to write and validate Playwright E2E tests more autonomously.
- Keep all workflows reproducible and lightweight, runnable on a laptop.

## Key Features Desired

- Run tests (unit/API/E2E) in a single command.
- Support linting, type checks, and test coverage.
- Be extendable to include build/deploy steps later.
- Allow Playwright trace-based test generation.
- Be language/tool agnostic where possible (works across Python, JS).

## Options for Local CI/CD Tooling

### 🛠️ 1. Taskfile (`Taskfile.yml`)
- **When to use**: If you want a clean, declarative task runner with minimal dependencies.
- **Pros**: Simple YAML, easy to extend, nice UX.
- **Cons**: Less common in some orgs; not natively tied to any specific CI service.

```yaml
# Example Taskfile
version: '3'

tasks:
  test:
    cmds:
      - pytest --cov=prompt_manager

  lint:
    cmds:
      - ruff check .
      - mypy prompt_manager/
      - eslint src/

  e2e:
    cmds:
      - npx playwright test

  all:
    deps: [lint, test, e2e]
````

### 🛠️ 2. Just (`Justfile`)

* **When to use**: If you prefer Makefile-style syntax but cleaner and more ergonomic.
* **Pros**: Fast, easy to onboard, expressive.
* **Cons**: Not environment-aware (you manage Python/Node setup separately).

### 🐳 3. Earthly

* **When to use**: If you want containerized reproducibility (e.g. multiple devs/environments).
* **Pros**: Works great with Docker, good for build/test/deploy pipelines.
* **Cons**: Requires Docker; Earthfile syntax is its own DSL.

### 🧪 4. GitHub Actions + `act` (local runner)

* **When to use**: If you already have GHA workflows or plan to deploy to GitHub.
* **Pros**: Same syntax as cloud CI; works locally via `act`.
* **Cons**: Some GHA actions don’t work perfectly in local emulation.

---

### ⚙️ 5. Make + Shell Scripts

* **When to use**: If you want absolute minimalism and know shell scripting well.
* **Pros**: Always available, no dependencies.
* **Cons**: Harder to scale, messy with many moving parts.

## Additional Playwright Workflow Enhancements

* **Trace-based Test Generation**:

  * Click through a flow manually.
  * Save the Playwright trace.
  * Have AI interpret the trace and write an E2E test.
  * Use prompts like:
    *"Here’s a trace log. Write a test that replicates this flow with retries + explicit selectors."*

* **Canonical Test Seeding**:

  * Include a few manually curated, clean Playwright tests.
  * AI can use these as patterns/templates for new tests.

* **Auto-scaffold New Route Tests**:

  * When a new frontend route is added, AI can generate a test scaffold that ensures basic rendering + navigation.
  * E.g., test skeletons that assert presence of key UI elements.

---

## Recommended Next Steps

1. Choose a task runner (`Taskfile`, `Just`, or `Make`) to orchestrate local steps.
2. Configure lint/type/test commands.
3. Set up Playwright with trace recording and define a convention for AI to consume + convert traces.
4. Gradually require test scaffolds for new features as part of the workflow.
5. Automate running this suite pre-merge or pre-push.

# Example Playwright capture prompt
```
You're a developer assistant. Convert the following Playwright trace into a fully working E2E test.

## Context:
The trace was captured during a manual walkthrough of a core user flow in the Prompt Manager application. The goal is to create a test that simulates the same user actions and asserts the expected outcomes.

## Instructions:
- Use `@playwright/test` syntax (TypeScript).
- Use explicit selectors (`data-testid`, `aria-label`, or `text=`), avoid auto-generated XPaths.
- Add `await expect()` assertions at each major step (e.g. page load, modal open, submission).
- If something failed in the trace, infer the fix (e.g. add `await page.waitForSelector(...)`).
- Keep the test file organized: setup, actions, assertions.
- At the end, include a summary comment of what the test validates.

## Trace File:
<insert path or upload trace.zip here>

## Additional Hints:
- The user logs in with test credentials (`user@example.com`, `password123`).
- They navigate to `/prompts`, click “New Prompt”, fill out a title, select a model, and submit.
- After submission, the prompt appears in the list and a toast notification confirms success.

Write a test file named `prompt-creation.spec.ts` that captures this behavior.
```

## Outcome

A fully local, developer-friendly CI pipeline that improves confidence in AI-generated code and tests, reduces regressions, and enables faster iteration with less human-in-the-loop effort.

[[project_maintenance_rules]]
