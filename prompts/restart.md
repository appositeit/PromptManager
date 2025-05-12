---
description: Prompt Manager restart prompt
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

Also, we should be able to rename a prompt, which will also require renaming the underlying file. We need to be careful to make sure the user can't accidentally rename to an existing file and over write it, but otherwise we should support a rename operation.

You have started implementing this change:

Now, let's add a rename functionality. I think the best place to add this would be in the prompt editor page, since that's where users are already editing the prompt. Let's add a "Rename" button in the prompt editor.
Now, let's add a modal dialog for renaming the prompt
Now, let's add the JavaScript to handle the rename functionality
Now, let's add the functions to handle showing the rename modal and performing the rename operation
Now, we need to add the backend API endpoint to handle renaming. Let's look at the prompt API implementation
Now, we need to add the backend API endpoint to handle renaming. Let's look at the prompt API implementation
Let's look at the unified_router.py which likely handles the prompts API
Let's look at router.py which is included first

Please continue.
