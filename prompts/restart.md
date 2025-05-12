---
description: Prompt Manager restart prompt
type: composite
---

We are working on a project called prompt manager, which we extracted from another project we developed called coordinator. I do a lot of prompt management and this standalone tool will be very useful.
The project directory is here:
/home/jem/development/prompt_manager/
The prompt manager running is now running on it's own. 

Some features of the prompt manager follow:

### Prompt Management
- `GET /api/prompts/fragments`: List all prompt fragments
- `GET /api/prompts/fragments/{fragment_id}`: Get a specific fragment
- `POST /api/prompts/fragments`: Create a new fragment
- `PUT /api/prompts/fragments/{fragment_id}`: Update a fragment
- `DELETE /api/prompts/fragments/{fragment_id}`: Delete a fragment
- `GET /api/prompts/templates`: List all prompt templates
- `GET /api/prompts/templates/{template_id}`: Get a specific template
- `POST /api/prompts/templates`: Create a new template
- `PUT /api/prompts/templates/{template_id}`: Update a template
- `DELETE /api/prompts/templates/{template_id}`: Delete a template
- `GET /api/prompts/templates/{template_id}/render`: Render a template with inclusions expanded
### WebSocket Interface
Connect to `/api/prompts/ws/fragments/{fragment_id}` for real-time fragment editing.

## Development
### Project Structure
```
prompt_manager/
├── bin/                # Helper scripts
├── config/             # Configuration files
├── doc/                # Documentation
├── src/                # Source code
│       ├── prompts/    # Prompt management system
│       │   ├── api/    # Prompt API
│       │   ├── models/ # Prompt data models
│       │   ├── services/ # Prompt services
│       │   ├── static/ # Static assets
│       │   └── templates/ # HTML templates
└── tests/              # Test cases
```

[[project_maintenance_rules]]

There is a "type" associated with each prompt. I don't think that is useful. Please remove "type" from the codebase, and make sure that type is removed from the metadata associated with each prompt so that we don't have problems loading prompts and their metadata.

When I try to update a directory entry, I click on the edit/pencil icon, make my change and click update, then browser freezes. There is a js error:manipulator.js:37 UncaughtF@manipulator.js:37getDataAttribute@manipulator.js:67_mergeConfigObj@config.js:41_getConfig@base-component.js:53W@base-component.js:33Nn@toast.js:53showToast@utils.js:46updateDirectory@prompts:1354updateDirectory@prompts:1357updateDirectory@prompts:1357updateDirectory@prompts:1357updateDirectory@prompts:1357The updateDirectory@prompts:1357 entries continue to repeat.