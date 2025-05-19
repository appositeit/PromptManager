"""
Service for managing MCP servers and configurations.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel
from src.models.mcp import RoleMCPConfig

# Define MCP models directly
class MCPServerConfig(BaseModel):
    id: str
    name: str
    url: str
    api_key: Optional[str] = None
    is_default: bool = False # Added from service logic
    status: Optional[str] = "unknown" # Added from service logic
    capabilities: Optional[List[str]] = [] # Added from service logic
    last_connected: Optional[datetime] = None # Added from service logic

class MCPToolConfig(BaseModel):
    tool_id: str
    name: str
    enabled: bool = True
    settings: Dict[str, Any] = {}

class MCPServerService:
    """Service for managing MCP servers and configurations."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the service with the data directory."""
        if data_dir is None:
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = base_dir.parent.parent / "data"
        
        self.data_dir = data_dir
        self.mcp_dir = data_dir / "mcp"
        self.mcp_dir.mkdir(parents=True, exist_ok=True)
        
        self.servers_file = self.mcp_dir / "servers.json"
        self.sessions_file = self.mcp_dir / "sessions.json"
        
        # Initialize with default data if files don't exist
        self._init_default_data()
    
    def _init_default_data(self) -> None:
        """Initialize default data if the files don't exist."""
        if not self.servers_file.exists():
            default_server = MCPServerConfig(
                id="default",
                name="Default MCP",
                url="http://localhost:8082",
                is_default=True,
                status="online",
                capabilities=["filesystem", "code_execution", "network"]
            )
            
            self.save_server(default_server)
        
        if not self.sessions_file.exists():
            with open(self.sessions_file, "w") as f:
                json.dump([], f)
    
    def get_servers(self) -> List[MCPServerConfig]:
        """Get all MCP servers."""
        if not self.servers_file.exists():
            return []
        
        with open(self.servers_file, "r") as f:
            data = json.load(f)
        
        return [MCPServerConfig(**item) for item in data]
    
    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        """Get a specific MCP server by ID."""
        servers = self.get_servers()
        for server in servers:
            if server.id == server_id:
                return server
        return None
    
    def save_server(self, server: MCPServerConfig) -> MCPServerConfig:
        """Save an MCP server config."""
        servers = self.get_servers()
        
        # Update or add the server
        for i, existing_server in enumerate(servers):
            if existing_server.id == server.id:
                servers[i] = server
                break
        else:
            servers.append(server)
        
        # If this is the default server, make sure no other server is default
        if server.is_default:
            for other_server in servers:
                if other_server.id != server.id:
                    other_server.is_default = False
        
        # Make sure at least one server is default
        if not any(s.is_default for s in servers):
            servers[0].is_default = True
        
        # Save to file
        with open(self.servers_file, "w") as f:
            json.dump([s.dict() for s in servers], f, default=str)
        
        return server
    
    def delete_server(self, server_id: str) -> bool:
        """Delete an MCP server config."""
        servers = self.get_servers()
        
        # Check if the server exists
        server = next((s for s in servers if s.id == server_id), None)
        if not server:
            return False
        
        # Remove the server
        servers = [s for s in servers if s.id != server_id]
        
        # Make sure at least one server is default if there are any servers left
        if servers and not any(s.is_default for s in servers):
            servers[0].is_default = True
        
        # Save to file
        with open(self.servers_file, "w") as f:
            json.dump([s.dict() for s in servers], f, default=str)
        
        return True
    
    def update_server_status(self, server_id: str, status: str) -> Optional[MCPServerConfig]:
        """Update the status of an MCP server."""
        server = self.get_server(server_id)
        if not server:
            return None
        
        server.status = status
        server.last_connected = datetime.now()
        
        return self.save_server(server)
    
    def get_role_configs(self, session_id: Optional[str] = None) -> List[RoleMCPConfig]:
        """Get MCP configurations for roles in sessions."""
        if not self.sessions_file.exists():
            return []
        
        with open(self.sessions_file, "r") as f:
            data = json.load(f)
        
        configs = [RoleMCPConfig(**item) for item in data]
        
        if session_id:
            configs = [c for c in configs if c.session_id == session_id]
        
        return configs
    
    def get_role_config(self, session_id: str, role_id: str) -> Optional[RoleMCPConfig]:
        """Get MCP configuration for a specific role in a session."""
        configs = self.get_role_configs(session_id)
        for config in configs:
            if config.session_id == session_id and config.role_id == role_id:
                return config
        return None
    
    def save_role_config(self, config: RoleMCPConfig) -> RoleMCPConfig:
        """Save MCP configuration for a role in a session."""
        configs = self.get_role_configs()
        
        # Update or add the config
        for i, existing_config in enumerate(configs):
            if existing_config.session_id == config.session_id and existing_config.role_id == config.role_id:
                configs[i] = config
                break
        else:
            configs.append(config)
        
        # Save to file
        with open(self.sessions_file, "w") as f:
            json.dump([c.dict() for c in configs], f)
        
        return config
    
    def delete_role_config(self, session_id: str, role_id: str) -> bool:
        """Delete MCP configuration for a role in a session."""
        configs = self.get_role_configs()
        
        # Remove the config
        configs = [c for c in configs if not (c.session_id == session_id and c.role_id == role_id)]
        
        # Save to file
        with open(self.sessions_file, "w") as f:
            json.dump([c.dict() for c in configs], f)
        
        return True
    
    def delete_session_configs(self, session_id: str) -> bool:
        """Delete all MCP configurations for a session."""
        configs = self.get_role_configs()
        
        # Remove configs for the session
        configs = [c for c in configs if c.session_id != session_id]
        
        # Save to file
        with open(self.sessions_file, "w") as f:
            json.dump([c.dict() for c in configs], f)
        
        return True
