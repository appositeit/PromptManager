# Server Management

This document describes how to manage the Prompt Manager server and its various administration features.

## Starting the Server

The recommended way to start the server is using the provided script:

```bash
./bin/start_prompt_manager.sh
```

This script provides several advantages:
- Sets up the virtual environment automatically if needed
- Creates timestamped log files for better debugging
- Checks for existing server instances to prevent port conflicts
- Sets up appropriate environment variables

For manual starting or custom configuration, you can also use:

```bash
# With default settings
python -m src.server

# With custom settings
python -m src.server --host 0.0.0.0 --port 8888 --log-level DEBUG
```

## Command Line Arguments

The server accepts the following command line arguments:

- `--host`: The host to bind to (default: 127.0.0.1)
- `--port`: The port to listen on (default: 8081)
- `--reload`: Enable auto-reload for development
- `--log-level`: Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: Specify a custom log file path

## Stopping the Server

The server provides two endpoints for stopping it:

### Immediate Stop

```bash
curl -X GET http://localhost:8081/api/stop
```

This endpoint immediately stops the server with minimal delay. It's ideal for scripts and automated processes. The server will send a quick response before terminating.

Response:
```json
{
  "message": "Server stopping immediately",
  "pid": 12345
}
```

### Graceful Shutdown

```bash
curl -X POST http://localhost:8081/api/shutdown
```

This endpoint initiates a graceful shutdown. The server will:
1. Process any pending requests
2. Send a shutdown response
3. Wait for a short delay (1 second)
4. Terminate itself

Response:
```json
{
  "message": "Server shutdown initiated"
}
```

## Log Files

The server creates timestamped log files in the `logs` directory. The naming convention is:

```
logs/prompt_manager_YYYYMMDDHHMMSS.log
```

A symlink called `logs/prompt_manager.log` always points to the latest log file for convenience.

The log files contain detailed information about:
- Server startup and configuration
- WebSocket connections and disconnections
- Prompt loading and management
- API requests and responses
- Errors and warnings

## Health Checks

You can check if the server is running properly with:

```bash
curl http://localhost:8081/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": "10:15:30",
  "prompts_loaded": 17,
  "directories": 3
}
```

## Process Management

If the server doesn't respond to stop commands, you can find and kill it manually:

```bash
# Find the process
ps aux | grep "src.server"

# Or more specifically
lsof -i :8081

# Kill the process
kill -9 <PID>
```

The `bin/restart_prompt_manager.sh` script combines stopping and starting in one command, which can be useful for quick resets during development.
