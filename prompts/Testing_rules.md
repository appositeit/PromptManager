## Testing
- Automate testing (unit, API, and E2E) locally.
- AI should write and validate Playwright E2E tests as autonomously as possible.
- Keep all workflows reproducible and lightweight, runnable on a laptop.
- Write unit tests, run and debug them for each file containing code, if
  coding is required. The unit tests should be written when the code is written.
  Code is not ready to run until the unit tests are written and pass. We aim for 80%
  test coverage.
- You should test for duplicated code. Duplicated code is bad. By default we use
  jscpd. It should be built into our test suite and available as a task. When we run
  tests, we check for duplicated code (python, javascript, html, css, etc). We exempt
  tests from duplication checking because tests are often better duplicated.

### Key Features Desired

- Run tests (unit/API/E2E) in a single command.
- Support linting, type checks, and test coverage.
- Be extendable to include build/deploy steps later.
- Allow Playwright trace-based test generation.
- Be language/tool agnostic where possible (works across Python, JS).

We will use Taskfile (`Taskfile.yml`) to have a clean and complete list of tasks related to
our project, and particularly our testing.

You MUST write unit tests for every module you write. These tests must pass before the work
is considered "done".
We should write integration tests for all our APIs.
We should have playwright tests for every web UI feature.
