---
description: Prompt Manager restart prompt
---

We are working on a project called prompt manager, which we extracted from another project we developed called coordinator. I do a lot of prompt management and this standalone tool is very useful.

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

There are some legacy concepts in the code such as "fragments". Fragments are functionally the same as prompts, I don't want them and I want all code and references to fragments removed.


# ToDo