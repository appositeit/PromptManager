# WebSocket API Testing Suite

This directory contains tooling and (soon) automated tests for the WebSocket API implementation in the Prompt Manager.

## Structure

- **test_websocket_tool.py**: A command-line utility to manually test WebSocket connections and interactions with various endpoints (prompts, debug, etc.). This can be useful for quick checks or diagnostics against a running server.
- **README_WEBSOCKET_TESTING.md**: This file, providing an overview of WebSocket testing for this project.

(Future additions may include pytest-based integration tests for automated WebSocket API validation.)

## Running the WebSocket Test Tool

Ensure the Prompt Manager server is running.

To use the tool:

```bash
# Example: Test a specific prompt WebSocket
python tests/integration/api/test_websocket_tool.py --type prompt --id my_prompt_id --port 8081

# Example: Test a generic debug WebSocket endpoint (assuming it's at /api/ws/test)
python tests/integration/api/test_websocket_tool.py --type generic --path /api/ws/test --port 8081
```

Refer to the tool's help for more options:
```bash
python tests/integration/api/test_websocket_tool.py --help
```

## Test Coverage Considerations (for future automated tests)

Automated WebSocket tests should cover aspects like:

1.  **Connection Management**:
    *   Successful client connections.
    *   Client disconnections (graceful and abrupt).
    *   Handling of connection attempts to invalid/non-existent prompt IDs.
2.  **Message Handling (for prompt WebSockets)**:
    *   Receiving initial prompt data upon connection.
    *   Sending updates from client to server (e.g., content changes) and verifying server processing.
    *   Receiving broadcasts from server (e.g., if another client modified the same prompt).
    *   Requesting specific actions (e.g., "expand_prompt") and validating the response.
    *   Error handling for invalid actions or malformed messages.
3.  **Authentication/Authorization** (if applicable to WebSockets).
4.  **Concurrency**: Multiple clients interacting with the same or different prompt WebSockets.

## Dependencies for the Test Tool

- `websockets`
- `asyncio`

(For future automated tests, `pytest` and `pytest-asyncio` would be typical.) 