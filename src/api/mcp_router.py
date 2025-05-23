"""
API routes for MCP server management.
"""

from typing import List
from fastapi import APIRouter, HTTPException

# Import models and service from the service module
from src.services.mcp import MCPServerService, MCPServerConfig, RoleMCPConfig
# Note: MCPToolConfig is defined in services.mcp but not directly used in this router's responses/requests yet.

# Create the router
router = APIRouter(prefix="/api/mcp", tags=["mcp"])

# Create the service instance using the imported service
# This will use the persistent service that saves to JSON files.
mcp_service = MCPServerService() # Initialize with default data_dir behavior from the service


@router.get("/servers", response_model=List[MCPServerConfig])
async def get_servers():
    """Get all MCP servers."""
    return mcp_service.get_servers()


@router.get("/servers/{server_id}", response_model=MCPServerConfig)
async def get_server(server_id: str):
    """Get a specific MCP server by ID."""
    server = mcp_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    return server


@router.post("/servers", response_model=MCPServerConfig)
async def create_server(server: MCPServerConfig):
    """Create a new MCP server."""
    existing = mcp_service.get_server(server.id)
    if existing:
        raise HTTPException(status_code=400, detail=f"MCP server '{server.id}' already exists")
    return mcp_service.save_server(server)


@router.put("/servers/{server_id}", response_model=MCPServerConfig)
async def update_server(server_id: str, server: MCPServerConfig):
    """Update an existing MCP server."""
    existing = mcp_service.get_server(server_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    
    # Ensure the ID matches
    if server.id != server_id:
        raise HTTPException(status_code=400, detail=f"Server ID in path '{server_id}' does not match ID in body '{server.id}'")
    
    return mcp_service.save_server(server)


@router.delete("/servers/{server_id}", response_model=bool)
async def delete_server(server_id: str):
    """Delete an MCP server."""
    existing = mcp_service.get_server(server_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"MCP server '{server_id}' not found")
    return mcp_service.delete_server(server_id)


@router.get("/session/{session_id}/roles", response_model=List[RoleMCPConfig])
async def get_session_role_configs(session_id: str):
    """Get all MCP configurations for roles in a session."""
    return mcp_service.get_role_configs(session_id)


@router.get("/session/{session_id}/role/{role_id}", response_model=RoleMCPConfig)
async def get_role_config(session_id: str, role_id: str):
    """Get MCP configuration for a specific role in a session."""
    config = mcp_service.get_role_config(session_id, role_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"MCP configuration for session '{session_id}', role '{role_id}' not found")
    return config


@router.post("/session/{session_id}/role/{role_id}", response_model=RoleMCPConfig)
async def create_role_config(session_id: str, role_id: str, config: RoleMCPConfig):
    """Create or update MCP configuration for a role in a session."""
    # Ensure the IDs match
    if config.session_id != session_id or config.role_id != role_id:
        raise HTTPException(
            status_code=400, 
            detail=f"IDs in path (session: '{session_id}', role: '{role_id}') do not match IDs in body (session: '{config.session_id}', role: '{config.role_id}')"
        )
    
    return mcp_service.save_role_config(config)


@router.delete("/session/{session_id}/role/{role_id}", response_model=bool)
async def delete_role_config(session_id: str, role_id: str):
    """Delete MCP configuration for a role in a session."""
    config = mcp_service.get_role_config(session_id, role_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"MCP configuration for session '{session_id}', role '{role_id}' not found")
    return mcp_service.delete_role_config(session_id, role_id)


@router.delete("/session/{session_id}", response_model=bool)
async def delete_session_configs(session_id: str):
    """Delete all MCP configurations for a session."""
    return mcp_service.delete_session_configs(session_id)
