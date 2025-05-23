# Prompt Manager

A standalone system for managing AI prompts with composable elements.

## Overview
Prompt Manager provides a web interface and API for creating, organizing, and managing prompts for AI interactions. It supports composable templates, prompt directories, and real-time editing. There is a focus on keyboard shortcuts and efficient workflow- directory listing and prompt embedding support tab completion, most interactions can be navigated using keyboard shortcuts, etc.

## Features
- Create and manage prompts (standard and composite)
- Compose templates with prompt inclusions and expansions
- Real-time editing via WebSocket (for prompts)
- Access prompts via RESTful API
- Render templates with all inclusions expanded
- Organize prompts in directories
- Integrates with Model Context Protocol (MCP) for advanced prompt workflows

## Quick Start
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd prompt_manager
   ```

2. Set up the environment (choose one):
   ```bash
   # Using Taskfile (recommended for full dev setup)
   task setup:py
   task setup:js
   task setup:e2e
   # Or using Makefile
   make setup
   ```

3. Run the application:
   ```bash
   ./bin/start_prompt_manager.sh
   # Or
   bin/restart_prompt_manager.sh
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
- `POST /api/prompts/expand`: Render a template with inclusions expanded
- `POST /api/prompts/rename`: Rename a prompt

### Directory Management
- `GET /api/prompts/directories/all`: List all prompt directories
- `POST /api/prompts/directories`: Add a new directory
- `DELETE /api/prompts/directories/{directory_path}`: Remove a directory
- `POST /api/prompts/reload`: Reload all prompts from all directories

## WebSocket Interface
- Connect to `/api/prompts/ws/{prompt_id}` for real-time prompt editing
- Uses standard WebSocket protocol with JSON messages for updates

## Configuration
The system uses several directories for prompt storage:
- Project data directory: `prompt_manager/data/prompts/`
- User config directory: `~/.prompt_manager/prompts/`

## MCP Integration
Prompt Manager supports integration with the Model Context Protocol (MCP) for advanced prompt workflows and Claude Desktop compatibility. See `mcp_server/` and related scripts for details.

## Development & Testing
- Run tests with `pytest` or using the provided Taskfile/Makefile targets.
- See `CHANGES.md` for recent updates and protocol fixes.
- See `README.md` in `mcp_server/` for MCP-specific details.

## License
Apache License 2.0. See [LICENSE](LICENSE).
