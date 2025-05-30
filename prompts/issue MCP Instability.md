# issue MCP Instability

We created an MCP server that provides access to Prompt Manager via an MCP server. The project directory for this is here:

`/home/jem/development/prompt_manager/mcp_server`

It doesn't seem to work properly- it has intermittently worked, but there are definitely current problemss.

In the doc directory read:
- project_overview.md
- implementation_plan.md

There is a large file which describes how LLMS shoudl work:
- llms-full.md    

It is too large to read in it's entirety. It's best to use an approach like:

/home/jem/bin/context.py
usage: context.py [-h] [-b BEFORE] [-a AFTER] [-m MATCH] keyword filepath
Example: context.py -b 10 -a 3 -m 2 'function' mycode.js

...and search for a word like transport to find out more about transport for MCPs.

Please adhere to normal project behaviours.

[[project_maintenance_rules]]

# Testing and Safety
Let's make comprehensive tests for the MCP server.

## Goals
- Automate testing (unit, API, and E2E) locally.
- Reduce human effort during feature rollout.
- Keep all workflows reproducible and lightweight, runnable on a laptop.

## Key Features Desired
- Run tests (unit/API/E2E) in a single command.
- Support linting, type checks, and test coverage.
- Be extendable to include build/deploy steps later.
- Be language/tool agnostic where possible (works across Python, JS).


## 🛠️ Taskfile (`Taskfile.yml`)
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

  all:
    deps: [lint, test, e2e]
````

## Recommended Next Steps

1. Choose a task runner (`Taskfile`, `Just`, or `Make`) to orchestrate local steps.
2. Configure lint/type/test commands.

## Outcome

A fully local, developer-friendly CI pipeline that improves confidence in AI-generated code and tests, reduces regressions, and enables faster iteration with less human-in-the-loop effort.

Let's use command line tools to debug the MCP server:

https://blog.fka.dev/blog/2025-03-25-inspecting-mcp-servers-using-cli/
