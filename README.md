# Prompt Manager

A standalone system for managing AI prompts with composable elements.

## Overview
Prompt Manager provides a web interface and API for creating, organizing, and managing prompts for AI interactions. It supports different prompt types, composable templates, and real-time collaborative editing.

## Features
- Create and manage different types of prompts (standard, composite, system, user)
- Compose templates with prompt inclusions and expansions
- Collaborate with real-time WebSocket editing
- Access prompts via RESTful API
- Render templates with all inclusions expanded

## Quick Start
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd prompt_manager
   ```

2. Set up the environment:
   ```bash
   bin/setup_venv.sh
   ```

3. Run the application:
   ```bash
   ./bin/start_prompt_manager.sh
   ```

4. Open your browser to http://localhost:8081

## Usage
The prompt manager can be used in two ways:
1. **Web Interface**: Access the web UI at http://localhost:8081
2. **API**: Use the RESTful API endpoints to programmatically manage prompts

## API Endpoints

### Prompt Management
- `GET /api/prompts/all`: List all prompts
- `GET /api/prompts/{prompt_id}`: Get a specific prompt
- `POST /api/prompts`: Create a new prompt
- `PUT /api/prompts/{prompt_id}`: Update a prompt
- `DELETE /api/prompts/{prompt_id}`: Delete a prompt
- `GET /api/prompts/{prompt_id}/render`: Render a template with inclusions expanded

### Fragment Management
- `GET /api/prompts/fragments`: List all fragments
- `GET /api/prompts/fragments/{fragment_id}`: Get a specific fragment
- `POST /api/prompts/fragments`: Create a new fragment
- `PUT /api/prompts/fragments/{fragment_id}`: Update a fragment
- `DELETE /api/prompts/fragments/{fragment_id}`: Delete a fragment

### Directory Management
- `GET /api/prompts/directories/all`: List all prompt directories
- `POST /api/prompts/directories`: Add a new directory
- `DELETE /api/prompts/directories/{directory_path}`: Remove a directory
- `POST /api/prompts/directories/{directory_path}/reload`: Reload prompts from a specific directory
- `POST /api/prompts/reload`: Reload all prompts from all directories

## WebSocket Interface
- Connect to `/api/prompts/ws/{prompt_id}` for real-time prompt editing
- Connect to `/api/prompts/ws/fragments/{fragment_id}` for real-time fragment editing
- Uses standard WebSocket protocol with JSON messages for updates

## Server Administration
- `GET /api/stop`: Immediately stop the server
- `POST /api/shutdown`: Gracefully shutdown the server after sending response
- The server has automatic log rotation with timestamped files

## Configuration
The system uses several directories for prompt storage:
- Project data directory: `prompt_manager/data/prompts/`
- User config directory: `~/.prompt_manager/prompts/`

## License
MIT
