---
description: Prompt Manager restart prompt
---

We are working on a project called prompt manager, which provides convenient prompt embdedding, shortcuts, etc.

The project directory is here:
`/home/jem/development/prompt_manager/`
The prompt manager running is now running on it's own. 

Please read:
`doc/server_management.md`
`doc/websocket_protocol.md`

## Development

Use the following scripts to start/stop/restart the server:
`bin/start_prompt_manager.sh`
`bin/stop_prompt_manager.sh`
`bin/restart_prompt_manager.sh`

The servers need a venv to run (as do the tests) these scripts make sure the venv is correctly initialised, they also do a safe shutdown of the servers if possible.

[[project_maintenance_rules]]

## Working with Prompt Manager

Use these scripts to manage stop/starting/restarting prompt manager:
bin/stop_prompt_manager.sh
bin/start_prompt_manager.sh
bin/restart_prompt_manager.sh  

Make sure to run:
make lint
make test

or
task ci:local

...before submitting any code changes.

# ToDo

Please complete the git commit.