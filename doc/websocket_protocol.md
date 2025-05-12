# WebSocket Protocol for Prompt Manager

This document describes the WebSocket protocol used for real-time editing in the Prompt Manager.

## Connection Endpoints

- **Prompts**: `/api/prompts/ws/{prompt_id}`
- **Fragments**: `/api/prompts/ws/fragments/{fragment_id}`
- **Debug**: `/debug/websocket` (test page for WebSocket connections)

## Message Format

All messages are JSON objects with an `action` field that determines the type of message.

### Server-to-Client Messages

#### Initial Message
Sent when a client connects to provide the initial state:

```json
{
  "action": "initial",
  "content": "...", // The current content of the prompt/fragment
  "description": "...", // The description metadata
  "tags": ["tag1", "tag2"], // Array of associated tags
  "prompt_type": "standard", // For prompts only - the type (standard, composite, system, user)
  "updated_at": "2025-05-11T17:41:28.226Z" // ISO8601 timestamp of last update
}
```

#### Update Status Message
Sent in response to update requests:

```json
{
  "action": "update_status",
  "success": true, // Whether the update was successful
  "timestamp": "2025-05-11T17:41:28.226Z" // ISO8601 timestamp of the update
}
```

#### Expanded Content Message
Sent in response to expansion requests:

```json
{
  "action": "expanded",
  "content": "...", // The original content with inclusions
  "expanded": "...", // The fully expanded content
  "dependencies": ["dep1", "dep2"], // List of prompt IDs that were included
  "warnings": [] // Any warnings about missing inclusions
}
```

#### Broadcast Update Message
Sent to all clients (except the sender) when an update occurs:

```json
{
  "action": "update",
  "content": "...", // The updated content
  "timestamp": "2025-05-11T17:41:28.226Z" // ISO8601 timestamp of the update
}
```

#### Broadcast Metadata Update Message
Sent to all clients (except the sender) when metadata is updated:

```json
{
  "action": "update_metadata",
  "description": "...", // The updated description
  "tags": ["tag1", "tag2"], // The updated tags
  "prompt_type": "standard", // For prompts only - the updated type
  "timestamp": "2025-05-11T17:41:28.226Z" // ISO8601 timestamp of the update
}
```

### Client-to-Server Messages

#### Update Content Request
Send to update the content of a prompt or fragment:

```json
{
  "action": "update",
  "content": "..." // The new content
}
```

#### Update Metadata Request
Send to update the metadata of a prompt or fragment:

```json
{
  "action": "update_metadata",
  "description": "...", // Optional - the new description
  "tags": ["tag1", "tag2"], // Optional - the new tags
  "prompt_type": "standard" // Optional, prompts only - the new prompt type
}
```

#### Expansion Request
Send to expand inclusions in a prompt or fragment:

```json
{
  "action": "expand",
  "content": "..." // The content to expand
}
```

## Error Handling

If a WebSocket connection fails, the client fallbacks to the REST API. The server will close WebSocket connections with error codes in these cases:

- `4004`: Prompt or fragment not found
- `1011`: Internal server error

## WebSocket Lifecycle

1. **Connection**: Client connects to the WebSocket endpoint
2. **Authentication**: No explicit authentication is required as long as the user has access to the server
3. **Initialization**: Server sends the initial state
4. **Message Exchange**: Client sends update requests, server responds with status and broadcasts changes
5. **Disconnection**: Connection is closed when the client disconnects or the server shuts down

## Example JavaScript Client

```javascript
// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8081/api/prompts/ws/${promptId}`);

// Handle connection open
ws.onopen = function() {
  console.log('Connected to WebSocket');
};

// Handle messages from server
ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  
  switch(message.action) {
    case 'initial':
      // Update UI with initial content
      editor.setValue(message.content);
      break;
    case 'update_status':
      // Show update status
      showToast(message.success ? 'Saved!' : 'Save failed');
      break;
    case 'update':
      // Update content from other clients
      editor.setValue(message.content);
      break;
    case 'expanded':
      // Show expanded content
      previewElement.innerHTML = message.expanded;
      break;
  }
};

// Send an update to the server
function sendUpdate(content) {
  ws.send(JSON.stringify({
    action: 'update',
    content: content
  }));
}

// Handle errors
ws.onerror = function(error) {
  console.error('WebSocket Error:', error);
  // Fall back to REST API
  fallbackToRestApi();
};

// Handle disconnection
ws.onclose = function(event) {
  console.log('WebSocket Closed:', event.code, event.reason);
  // Attempt reconnection
  setTimeout(reconnect, 3000);
};
```
