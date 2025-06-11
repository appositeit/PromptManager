# MCP Server Management Scripts

## Important: MCP Server Communication

MCP (Model Context Protocol) servers communicate via **STDIO** (standard input/output), not HTTP. This means:

- ❌ **Cannot run in background** (no `nohup` or `&`)
- ❌ **Cannot redirect stdout/stderr** (breaks MCP protocol)
- ✅ **Must run in foreground** with clean STDIO
- ✅ **All user messages go to stderr** (leaves stdout for MCP)

## Usage

### Multiple Instances
**Important**: Multiple MCP servers can run simultaneously. Each OCD instance or application can have its own MCP server instance. The start script will **never** prevent starting additional servers.

### Direct Command Line
```bash
# From project root with venv activated
python -m src.mcp_server.server
```

### Using Management Scripts

#### Start Server (Foreground)
```bash
./bin/start_mcp_server.sh
```
This will:
- Activate the virtual environment
- Run the MCP server in foreground
- Handle STDIO properly for MCP communication
- **Always start a new instance** (no conflict checking)

#### Check if Running
```bash
./bin/isalive_mcp_server.sh
```
Shows all running MCP server instances.

#### Stop Server
```bash
./bin/stop_mcp_server.sh
```
This finds and gracefully terminates **ALL** MCP server processes for this project.

#### Restart Server
```bash
./bin/restart_mcp_server.sh
```
Stops all instances and starts a single new one.

## Integration with Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "prompt-manager": {
    "command": "/home/jem/development/prompt_manager/bin/start_mcp_server.sh",
    "args": []
  }
}
```

## Testing

Test the server with the provided client:
```bash
./bin/test_mcp_client.py
```

This validates that the server is properly responding to MCP protocol messages.

## Available Tools

The MCP server provides these tools:
- `list_prompts` - List all available prompts
- `get_prompt` - Get specific prompt by ID  
- `search_prompts` - Search prompts by text content
- `expand_prompt` - Expand prompt with all inclusions resolved
- `create_prompt` - Create new prompt
- `update_prompt` - Update existing prompt  
- `delete_prompt` - Delete prompt
