"""
MCP Server implementation for Prompt Manager.

AI-generated on 2025-06-07
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.prompt_service import PromptService
from src.models.unified_prompt import Prompt

logger = logging.getLogger(__name__)


@dataclass 
class MCPRequest:
    """Represents an MCP request."""
    id: str
    method: str
    params: Dict[str, Any]


@dataclass
class MCPResponse:
    """Represents an MCP response."""
    id: str
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class PromptManagerMCPServer:
    """MCP Server that exposes Prompt Manager functionality."""
    
    def __init__(self, host: str = "localhost", port: int = 8083):
        self.host = host
        self.port = port
        self.prompt_service: Optional[PromptService] = None
        self.server = None
        
        # Initialize prompt service
        try:
            self.prompt_service = PromptService(base_directories=None, auto_load=True)
            logger.info(f"Initialized PromptService with {len(self.prompt_service.prompts)} prompts")
        except Exception as e:
            logger.error(f"Failed to initialize PromptService: {e}")
            
    async def start(self):
        """Start the MCP server."""
        import asyncio
        
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            logger.info(f"MCP Server started on {self.host}:{self.port}")
            
            # Serve forever
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
            
    async def stop(self):
        """Stop the MCP server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("MCP Server stopped")
            
    async def handle_client(self, reader, writer):
        """Handle a client connection."""
        peer = writer.get_extra_info('peername')
        logger.info(f"Client connected from {peer}")
        
        try:
            while True:
                # Read JSON-RPC message
                data = await reader.readline()
                if not data:
                    break
                    
                try:
                    message = json.loads(data.decode().strip())
                    request = MCPRequest(
                        id=message.get('id', ''),
                        method=message.get('method', ''),
                        params=message.get('params', {})
                    )
                    
                    # Process request
                    response = await self.handle_request(request)
                    
                    # Send response
                    response_data = {
                        'id': response.id,
                        'jsonrpc': '2.0'
                    }
                    
                    if response.error:
                        response_data['error'] = response.error
                    else:
                        response_data['result'] = response.result
                        
                    response_json = json.dumps(response_data) + '\n'
                    writer.write(response_json.encode())
                    await writer.drain()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from client: {e}")
                    error_response = {
                        'id': None,
                        'jsonrpc': '2.0',
                        'error': {
                            'code': -32700,
                            'message': 'Parse error'
                        }
                    }
                    writer.write((json.dumps(error_response) + '\n').encode())
                    await writer.drain()
                    
        except asyncio.CancelledError:
            logger.info("Client handler cancelled")
        except Exception as e:
            logger.error(f"Error handling client {peer}: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            logger.info(f"Client {peer} disconnected")
            
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request and return a response."""
        try:
            if request.method == 'tools/list':
                return await self.list_tools(request)
            elif request.method == 'tools/call':
                return await self.call_tool(request)
            elif request.method == 'initialize':
                return await self.initialize(request)
            elif request.method == 'ping':
                return MCPResponse(id=request.id, result={'status': 'pong'})
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        'code': -32601,
                        'message': f'Method not found: {request.method}'
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling request {request.method}: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            )
            
    async def initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialization request."""
        return MCPResponse(
            id=request.id,
            result={
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {},
                },
                'serverInfo': {
                    'name': 'prompt-manager-mcp',
                    'version': '1.0.0'
                }
            }
        )
        
    async def list_tools(self, request: MCPRequest) -> MCPResponse:
        """List available tools."""
        tools = [
            {
                'name': 'list_prompts',
                'description': 'List all available prompts',
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            {
                'name': 'get_prompt',
                'description': 'Get a specific prompt by ID',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'prompt_id': {
                            'type': 'string',
                            'description': 'The ID of the prompt to retrieve'
                        }
                    },
                    'required': ['prompt_id']
                }
            },
            {
                'name': 'search_prompts',
                'description': 'Search prompts by text content',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'Search query to find prompts'
                        }
                    },
                    'required': ['query']
                }
            },
            {
                'name': 'expand_prompt',
                'description': 'Expand a prompt with all inclusions resolved',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'prompt_id': {
                            'type': 'string',
                            'description': 'The ID of the prompt to expand'
                        }
                    },
                    'required': ['prompt_id']
                }
            },
            {
                'name': 'create_prompt',
                'description': 'Create a new prompt',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'prompt_id': {
                            'type': 'string',
                            'description': 'Unique ID for the new prompt'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'Content of the prompt'
                        },
                        'directory': {
                            'type': 'string',
                            'description': 'Directory to create the prompt in (optional)'
                        }
                    },
                    'required': ['prompt_id', 'content']
                }
            },
            {
                'name': 'update_prompt',
                'description': 'Update an existing prompt',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'prompt_id': {
                            'type': 'string',
                            'description': 'ID of the prompt to update'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'New content for the prompt'
                        }
                    },
                    'required': ['prompt_id', 'content']
                }
            },
            {
                'name': 'delete_prompt',
                'description': 'Delete a prompt',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'prompt_id': {
                            'type': 'string',
                            'description': 'ID of the prompt to delete'
                        }
                    },
                    'required': ['prompt_id']
                }
            }
        ]
        
        return MCPResponse(id=request.id, result={'tools': tools})
        
    async def call_tool(self, request: MCPRequest) -> MCPResponse:
        """Call a specific tool."""
        if not self.prompt_service:
            return MCPResponse(
                id=request.id,
                error={
                    'code': -32603,
                    'message': 'PromptService not initialized'
                }
            )
            
        params = request.params
        tool_name = params.get('name', '')
        arguments = params.get('arguments', {})
        
        try:
            if tool_name == 'list_prompts':
                result = await self.tool_list_prompts(arguments)
            elif tool_name == 'get_prompt':
                result = await self.tool_get_prompt(arguments)
            elif tool_name == 'search_prompts':
                result = await self.tool_search_prompts(arguments)
            elif tool_name == 'expand_prompt':
                result = await self.tool_expand_prompt(arguments)
            elif tool_name == 'create_prompt':
                result = await self.tool_create_prompt(arguments)
            elif tool_name == 'update_prompt':
                result = await self.tool_update_prompt(arguments)
            elif tool_name == 'delete_prompt':
                result = await self.tool_delete_prompt(arguments)
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        'code': -32601,
                        'message': f'Tool not found: {tool_name}'
                    }
                )
                
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    'code': -32603,
                    'message': f'Tool execution error: {str(e)}'
                }
            )
            
    # Tool implementations
    async def tool_list_prompts(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List all prompts."""
        prompts = []
        for prompt in self.prompt_service.prompts.values():
            prompts.append({
                'id': prompt.id,
                'unique_id': prompt.unique_id,
                'directory': prompt.directory,
                'path': str(prompt.path) if prompt.path else None,
                'content_preview': prompt.content[:100] + '...' if len(prompt.content) > 100 else prompt.content
            })
            
        return {
            'prompts': prompts,
            'total_count': len(prompts)
        }
        
    async def tool_get_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt."""
        prompt_id = arguments['prompt_id']
        prompt = self.prompt_service.get_prompt(prompt_id)
        
        if not prompt:
            raise ValueError(f"Prompt '{prompt_id}' not found")
            
        return {
            'id': prompt.id,
            'unique_id': prompt.unique_id,
            'directory': prompt.directory,
            'path': str(prompt.path) if prompt.path else None,
            'content': prompt.content
        }
        
    async def tool_search_prompts(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search prompts by content."""
        query = arguments['query'].lower()
        matching_prompts = []
        
        for prompt in self.prompt_service.prompts.values():
            if query in prompt.content.lower() or query in prompt.id.lower():
                matching_prompts.append({
                    'id': prompt.id,
                    'unique_id': prompt.unique_id,
                    'directory': prompt.directory,
                    'path': str(prompt.path) if prompt.path else None,
                    'content_preview': prompt.content[:200] + '...' if len(prompt.content) > 200 else prompt.content
                })
                
        return {
            'prompts': matching_prompts,
            'query': arguments['query'],
            'total_count': len(matching_prompts)
        }
        
    async def tool_expand_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Expand a prompt with all inclusions."""
        prompt_id = arguments['prompt_id']
        prompt = self.prompt_service.get_prompt(prompt_id)
        
        if not prompt:
            raise ValueError(f"Prompt '{prompt_id}' not found")
            
        expanded_content, dependencies, warnings = self.prompt_service.expand_inclusions(
            prompt.content, parent_id=prompt.id
        )
        
        return {
            'id': prompt.id,
            'expanded_content': expanded_content,
            'dependencies': list(dependencies),
            'warnings': warnings
        }
        
    async def tool_create_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt."""
        prompt_id = arguments['prompt_id']
        content = arguments['content']
        directory = arguments.get('directory')
        
        # Use the first available directory if none specified
        if not directory and self.prompt_service.directories:
            directory = list(self.prompt_service.directories.keys())[0]
            
        if not directory:
            raise ValueError("No directories available for creating prompts")
            
        # Create the prompt
        success = self.prompt_service.create_prompt(prompt_id, content, directory)
        
        if not success:
            raise ValueError(f"Failed to create prompt '{prompt_id}'")
            
        # Reload to get the new prompt
        self.prompt_service.reload_prompts()
        prompt = self.prompt_service.get_prompt(prompt_id)
        
        return {
            'id': prompt.id,
            'unique_id': prompt.unique_id,
            'directory': prompt.directory,
            'content': prompt.content,
            'created': True
        }
        
    async def tool_update_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing prompt."""
        prompt_id = arguments['prompt_id']
        content = arguments['content']
        
        prompt = self.prompt_service.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt '{prompt_id}' not found")
            
        success = self.prompt_service.update_prompt(prompt_id, content)
        
        if not success:
            raise ValueError(f"Failed to update prompt '{prompt_id}'")
            
        # Reload to get updated content
        self.prompt_service.reload_prompts()
        updated_prompt = self.prompt_service.get_prompt(prompt_id)
        
        return {
            'id': updated_prompt.id,
            'unique_id': updated_prompt.unique_id,
            'directory': updated_prompt.directory,
            'content': updated_prompt.content,
            'updated': True
        }
        
    async def tool_delete_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a prompt."""
        prompt_id = arguments['prompt_id']
        
        prompt = self.prompt_service.get_prompt(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt '{prompt_id}' not found")
            
        success = self.prompt_service.delete_prompt(prompt_id)
        
        if not success:
            raise ValueError(f"Failed to delete prompt '{prompt_id}'")
            
        # Reload to confirm deletion
        self.prompt_service.reload_prompts()
        
        return {
            'id': prompt_id,
            'deleted': True
        }


# Main entry point
async def main():
    """Main entry point for running the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = PromptManagerMCPServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server...")
        await server.stop()
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
