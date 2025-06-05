---
description: Prompt Manager restart prompt
---

We are working on a project called prompt manager, which provides convenient prompt embdedding, shortcuts, etc.

The project directory is here:
`/home/jem/development/prompt_manager/`


# Development

[[project_maintenance_rules]]

## Working with Prompt Manager

* The servers need a venv to run (as do the tests) these scripts make sure the venv is correctly initialised, they also do a safe shutdown of the servers if possible. Use these scripts to manage stop/starting/restarting prompt manager:
`bin/start_prompt_manager.sh`
`bin/stop_prompt_manager.sh`
`bin/restart_prompt_manager.sh`

* Before git submitting any code changes make sure to run:
```
make lint
make test
# or
task ci:local
```


# ToDo

When we add or remove a directory, the prompt list should automatically reload- as it is we have to manually hit the Reload All button.