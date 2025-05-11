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
   bin/run_prompt_manager.py
   ```

4. Open your browser to http://localhost:8081

## Usage
The prompt manager can be used in two ways:
1. **Web Interface**: Access the web UI at http://localhost:8081
2. **API**: Use the RESTful API endpoints to programmatically manage prompts

## API Endpoints
- `GET /api/prompts`: List all prompts
- `GET /api/prompts/{prompt_id}`: Get a specific prompt
- `POST /api/prompts`: Create a new prompt
- `PUT /api/prompts/{prompt_id}`: Update a prompt
- `DELETE /api/prompts/{prompt_id}`: Delete a prompt
- `GET /api/prompts/{prompt_id}/render`: Render a template with inclusions expanded

## WebSocket Interface
- Connect to `/api/prompts/ws/prompts/{prompt_id}` for real-time prompt editing

## Configuration
The system uses several directories for prompt storage:
- Project data directory: `prompt_manager/data/prompts/`
- User config directory: `~/.prompt_manager/prompts/`

## License
MIT
