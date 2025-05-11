"""
Models for MCP server management.
"""

from datetime import datetime
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, validator


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    
    id: str = Field(..., description="Unique identifier for the MCP server")
    name: str = Field(..., description="Display name for the MCP server")
    url: str = Field(..., description="URL of the MCP server")
    api_key: Optional[str] = Field(None, description="API key for the MCP server")
    is_default: bool = Field(False, description="Whether this is the default MCP server")
    created_at: datetime = Field(default_factory=datetime.now, description="When the server was added")
    last_connected: Optional[datetime] = Field(None, description="When the server was last connected to")
    status: str = Field("unknown", description="Current status of the MCP server")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities provided by this MCP server")


class MCPToolConfig(BaseModel):
    """Configuration for an MCP tool."""
    
    tool_id: str = Field(..., description="Tool ID")
    name: str = Field(..., description="Display name for the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    is_enabled: bool = Field(True, description="Whether the tool is enabled")
    config: Dict[str, Union[str, int, float, bool]] = Field(
        default_factory=dict, description="Tool-specific configuration"
    )


class RoleMCPConfig(BaseModel):
    """Configuration for MCP access for a specific role in a session."""
    
    session_id: str = Field(..., description="Session ID")
    role_id: str = Field(..., description="Role ID (e.g., 'architect', 'worker1')")
    servers: List[str] = Field(default_factory=list, description="List of MCP server IDs")
    tool_overrides: Dict[str, Dict[str, bool]] = Field(
        default_factory=dict, 
        description="Overrides for specific tools by server ID and tool ID"
    )
    api_key_overrides: Dict[str, str] = Field(
        default_factory=dict,
        description="API key overrides by server ID"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session123",
                "role_id": "architect",
                "servers": ["default", "mcp2"],
                "tool_overrides": {
                    "default": {
                        "filesystem_tools": True,
                        "code_execution": True,
                        "network_tools": False
                    }
                },
                "api_key_overrides": {
                    "default": "custom_api_key_for_architect"
                }
            }
        }
