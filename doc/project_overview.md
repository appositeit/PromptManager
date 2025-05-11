# Prompt Manager

## Overview
Prompt Manager is a standalone application for creating, organizing, and managing AI prompts. It provides a web interface and API for prompt management with composable elements, allowing you to create reusable prompt fragments and templates.

Originally developed as part of the [Coordinator](https://github.com/example/coordinator) project for multi-agent AI orchestration, Prompt Manager has been extracted into its own project for broader usability.

## Key Features
- **Unified Prompt Management**: Manage different types of prompts (standard, composite, system, user)
- **Composable Templates**: Create reusable templates with prompt inclusions
- **Web Interface**: User-friendly interface for creating and editing prompts
- **API Access**: RESTful API for programmatic prompt management
- **WebSocket Support**: Real-time collaborative editing of prompts
- **Prompt Rendering**: Expand composite prompts into their final form

## System Architecture
The Prompt Manager is built with modern Python web technologies:

- **FastAPI**: High-performance web framework for the API and web interface
- **Jinja2**: Template engine for HTML rendering
- **Uvicorn**: ASGI server for serving the application
- **WebSockets**: For real-time collaborative editing

### Core Components
- **Prompt Service**: Core service for managing prompt CRUD operations
- **API Layer**: RESTful endpoints for prompt management
- **Web Interface**: User-friendly interface for prompt management
- **Storage System**: File-based storage for prompts with configurable directories

## API Endpoints
The system provides several API endpoints:

### Prompt Management
- `GET /api/prompts`: List all prompts
- `GET /api/prompts/{prompt_id}`: Get a specific prompt
- `POST /api/prompts`: Create a new prompt
- `PUT /api/prompts/{prompt_id}`: Update a prompt
- `DELETE /api/prompts/{prompt_id}`: Delete a prompt
- `GET /api/prompts/{prompt_id}/render`: Render a template with inclusions expanded

### WebSocket Interface
- Connect to `/api/prompts/ws/prompts/{prompt_id}` for real-time prompt editing

## Directory Structure
```
prompt_manager/
├── bin/                # Helper scripts
├── config/             # Configuration files
├── doc/                # Documentation
│   └── progress/       # Progress updates
├── logs/               # Application logs
├── src/                # Source code
│   ├── api/            # API endpoints
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   ├── static/         # Static assets
│   ├── templates/      # HTML templates
│   ├── app.py          # Application entry point
│   └── server.py       # Server configuration
└── tests/              # Test cases
```

## Development
### Setup
1. Clone the repository
2. Run the setup script to create a virtual environment:
   ```bash
   bin/setup_venv.sh
   ```
3. Start the server:
   ```bash
   bin/run_prompt_manager.py
   ```

### Configuration
The system uses several directories for prompt storage:
- Project data directory: `prompt_manager/data/prompts/`
- User config directory: `~/.prompt_manager/prompts/`

You can add additional directories through the API or web interface.

## License
MIT
