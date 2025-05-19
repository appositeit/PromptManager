"""
Models for MCP server management.
"""

from datetime import datetime
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field


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
    session_id: str
    role_id: str
    config: dict = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
