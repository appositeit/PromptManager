"""
WebSocket routes for real-time editing of prompts and fragments.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from loguru import logger

from src.services.prompt_service import PromptService

# Create router
router = APIRouter()

# Get prompt service singleton
def get_prompt_service():
    """Get the prompt service singleton."""
    from src.api.router import get_prompt_service as get_service
    return get_service()

# Get fragment service singleton
def get_fragment_service():
    """Get the fragment service singleton."""
    from src.api.fragments_router import get_fragment_service as get_service
    return get_service()

# Connection manager for WebSockets
class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, prompt_id: str):
        """Connect a WebSocket client."""
        await websocket.accept()
        
        if prompt_id not in self.connections:
            self.connections[prompt_id] = []
        
        self.connections[prompt_id].append(websocket)
        logger.debug(f"WebSocket client connected to prompt {prompt_id}")
    
    def disconnect(self, websocket: WebSocket, prompt_id: str):
        """Disconnect a WebSocket client."""
        if prompt_id in self.connections:
            if websocket in self.connections[prompt_id]:
                self.connections[prompt_id].remove(websocket)
                logger.debug(f"WebSocket client disconnected from prompt {prompt_id}")
            
            # Clean up empty lists
            if not self.connections[prompt_id]:
                del self.connections[prompt_id]
    
    async def broadcast(self, message: Dict, prompt_id: str, exclude: Optional[WebSocket] = None):
        """Broadcast a message to all clients except the one specified."""
        if prompt_id in self.connections:
            for websocket in self.connections[prompt_id]:
                if websocket != exclude:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to client: {str(e)}")

# Create connection manager
manager = ConnectionManager()

@router.websocket("/api/prompts/ws/{prompt_id}")
async def websocket_endpoint(websocket: WebSocket, prompt_id: str):
    """WebSocket endpoint for real-time prompt editing."""
    prompt_service = get_prompt_service()
    
    # Get the prompt
    prompt = prompt_service.get_prompt(prompt_id)
    if not prompt:
        await websocket.close(code=4004, reason=f"Prompt '{prompt_id}' not found")
        return
    
    # Accept the connection
    await manager.connect(websocket, prompt_id)
    
    # Send initial data
    try:
        await websocket.send_json({
            "action": "initial",
            "content": prompt.content,
            "description": prompt.description,
            "tags": prompt.tags,
            "prompt_type": prompt.prompt_type,
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None
        })
    except Exception as e:
        logger.error(f"Error sending initial data: {str(e)}")
        manager.disconnect(websocket, prompt_id)
        return
    
    # Handle messages
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            action = data.get("action")
            
            # Handle update
            if action == "update":
                content = data.get("content")
                if content is not None:
                    # Update prompt content
                    prompt.content = content
                    now = datetime.now(timezone.utc)
                    prompt.updated_at = now
                    
                    # Save to disk
                    success = prompt_service.save_prompt(prompt)
                    
                    # Send status
                    await websocket.send_json({
                        "action": "update_status",
                        "success": success,
                        "timestamp": now.isoformat()
                    })
                    
                    # Broadcast update to other clients
                    await manager.broadcast({
                        "action": "update",
                        "content": content,
                        "timestamp": now.isoformat()
                    }, prompt_id, exclude=websocket)
            
            # Handle metadata update
            elif action == "update_metadata":
                description = data.get("description")
                tags = data.get("tags")
                prompt_type = data.get("prompt_type")
                
                # Update prompt metadata
                if description is not None:
                    prompt.description = description
                
                if tags is not None:
                    prompt.tags = tags
                
                if prompt_type is not None:
                    prompt.prompt_type = prompt_type
                
                now = datetime.now(timezone.utc)
                prompt.updated_at = now
                
                # Save to disk
                success = prompt_service.save_prompt(prompt)
                
                # Send status
                await websocket.send_json({
                    "action": "update_status",
                    "success": success,
                    "timestamp": now.isoformat()
                })
                
                # Broadcast update to other clients
                await manager.broadcast({
                    "action": "update_metadata",
                    "description": description,
                    "tags": tags,
                    "prompt_type": prompt_type,
                    "timestamp": now.isoformat()
                }, prompt_id, exclude=websocket)
            
            # Handle expansion request
            elif action == "expand":
                content = data.get("content")
                if content is not None:
                    # Expand content
                    expanded, dependencies, warnings = prompt_service.expand_inclusions(content, root_id=prompt_id)
                    
                    # Send expanded content
                    await websocket.send_json({
                        "action": "expanded",
                        "content": content,
                        "expanded": expanded,
                        "dependencies": list(dependencies),
                        "warnings": warnings
                    })
    
    except WebSocketDisconnect:
        logger.debug(f"WebSocket client disconnected from prompt {prompt_id}")
    except Exception as e:
        logger.opt(exception=True).error(f"Error in WebSocket connection: {str(e)}")
    finally:
        # Disconnect client
        manager.disconnect(websocket, prompt_id)

@router.websocket("/api/prompts/ws/fragments/{fragment_id}")
async def fragment_websocket_endpoint(websocket: WebSocket, fragment_id: str):
    """WebSocket endpoint for real-time fragment editing."""
    fragment_service = get_fragment_service()
    
    # Get the fragment
    fragment = fragment_service.get_fragment(fragment_id)
    if not fragment:
        await websocket.close(code=4004, reason=f"Fragment '{fragment_id}' not found")
        return
    
    # Accept the connection
    await manager.connect(websocket, fragment_id)
    
    # Send initial data
    try:
        await websocket.send_json({
            "action": "initial",
            "content": fragment.content,
            "description": fragment.description,
            "tags": fragment.tags,
            "updated_at": fragment.updated_at.isoformat() if fragment.updated_at else None
        })
    except Exception as e:
        logger.error(f"Error sending initial data: {str(e)}")
        manager.disconnect(websocket, fragment_id)
        return
    
    # Handle messages
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            action = data.get("action")
            
            # Handle update
            if action == "update":
                content = data.get("content")
                if content is not None:
                    # Update fragment content
                    fragment.content = content
                    now = datetime.now(timezone.utc)
                    fragment.updated_at = now
                    
                    # Save to disk
                    success = fragment_service.save_fragment(fragment)
                    
                    # Send status
                    await websocket.send_json({
                        "action": "update_status",
                        "success": success,
                        "timestamp": now.isoformat()
                    })
                    
                    # Broadcast update to other clients
                    await manager.broadcast({
                        "action": "update",
                        "content": content,
                        "timestamp": now.isoformat()
                    }, fragment_id, exclude=websocket)
            
            # Handle metadata update
            elif action == "update_metadata":
                description = data.get("description")
                tags = data.get("tags")
                
                # Update fragment metadata
                if description is not None:
                    fragment.description = description
                
                if tags is not None:
                    fragment.tags = tags
                
                now = datetime.now(timezone.utc)
                fragment.updated_at = now
                
                # Save to disk
                success = fragment_service.save_fragment(fragment)
                
                # Send status
                await websocket.send_json({
                    "action": "update_status",
                    "success": success,
                    "timestamp": now.isoformat()
                })
                
                # Broadcast update to other clients
                await manager.broadcast({
                    "action": "update_metadata",
                    "description": description,
                    "tags": tags,
                    "timestamp": now.isoformat()
                }, fragment_id, exclude=websocket)
            
            # Handle expansion request
            elif action == "expand":
                content = data.get("content")
                if content is not None:
                    # Expand content - this works with fragments too
                    # using the same expansion function
                    prompt_service = get_prompt_service()
                    expanded, dependencies, warnings = prompt_service.expand_inclusions(content, root_id=fragment_id)
                    
                    # Send expanded content
                    await websocket.send_json({
                        "action": "expanded",
                        "content": content,
                        "expanded": expanded,
                        "dependencies": list(dependencies),
                        "warnings": warnings
                    })
    
    except WebSocketDisconnect:
        logger.debug(f"WebSocket client disconnected from fragment {fragment_id}")
    except Exception as e:
        logger.opt(exception=True).error(f"Error in WebSocket connection: {str(e)}")
    finally:
        # Disconnect client
        manager.disconnect(websocket, fragment_id)
