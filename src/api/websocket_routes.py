"""
WebSocket routes for real-time editing of prompts and fragments.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.services.prompt_service import PromptService

# Store for the PromptService instance, to be set by server.py
# This bypasses potential issues with FastAPI dependency_overrides for WebSockets.
websocket_prompt_service_store: Optional[PromptService] = None

async def get_ws_prompt_service() -> PromptService:
    logger.debug(f"get_ws_prompt_service called. websocket_prompt_service_store is set: {websocket_prompt_service_store is not None}")
    if websocket_prompt_service_store:
        return websocket_prompt_service_store
    # This error indicates a setup problem in server.py
    raise NotImplementedError("PromptService instance not provided to websocket_routes module.")

# Create router 
router = APIRouter(tags=["websockets"])

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
            for websocket_client in self.connections[prompt_id]: # Renamed websocket to websocket_client to avoid conflict with outer scope
                if websocket_client != exclude:
                    try:
                        await websocket_client.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to client: {str(e)}")

# Create connection manager
manager = ConnectionManager()

@router.websocket("/ws/prompts/{prompt_id}", name="ws_prompt")
async def websocket_endpoint(websocket: WebSocket, prompt_id: str):
    try:
        logger.debug(f"WebSocket EP ({prompt_id}): Entry (Top Level Try)")
        
        logger.debug(f"WebSocket EP ({prompt_id}): Attempting to get prompt_service via get_ws_prompt_service")
        prompt_service = await get_ws_prompt_service()
        logger.debug(f"WebSocket EP ({prompt_id}): get_ws_prompt_service returned type: {type(prompt_service)}, is None: {prompt_service is None}")
        
        if prompt_service is None:
            logger.error(f"WebSocket EP ({prompt_id}): Critical error - prompt_service_instance is None!")
            try:
                await websocket.close(code=1011, reason="Server configuration error: Prompt service unavailable")
            except Exception as close_exc:
                logger.warning(f"WebSocket EP ({prompt_id}): Exception during websocket.close after prompt_service was None: {close_exc}", exc_info=True)
            return

        logger.debug(f"WebSocket EP ({prompt_id}): Attempting prompt_service.get_prompt('{prompt_id}') (PS id: {id(prompt_service)})")
        prompt = prompt_service.get_prompt(prompt_id)
        logger.debug(f"WebSocket EP ({prompt_id}): get_prompt returned type: {type(prompt)}. Value: {prompt!r}")
        logger.debug(f"WebSocket EP ({prompt_id}): Evaluation of 'not prompt': {not prompt}")

        if not prompt:
            logger.warning(f"WebSocket EP ({prompt_id}): Prompt not found by service. Closing with 4004.")
            try:
                await websocket.close(code=4004, reason=f"Prompt '{prompt_id}' not found")
            except Exception as close_exc:
                logger.warning(f"WebSocket EP ({prompt_id}): Exception during websocket.close after prompt not found: {close_exc}", exc_info=True)
            return
        
        logger.info(f"WebSocket EP ({prompt_id}): Prompt found. Name: '{getattr(prompt, 'name', prompt.id)}', Unique ID: '{prompt.unique_id}'")
        logger.debug(f"WebSocket EP ({prompt_id}): All checks passed, proceeding to manager.connect")
        
        # This inner try-except is for manager.connect and subsequent operations
        try:
            logger.debug(f"WebSocket EP ({prompt_id}): Inside inner try, attempting manager.connect (will call websocket.accept())")
            await manager.connect(websocket, prompt_id)
            logger.info(f"WebSocket EP ({prompt_id}): manager.connect succeeded (websocket.accept() called).")
        except WebSocketDisconnect:
            logger.warning(f"WebSocket EP ({prompt_id}): WebSocketDisconnect during/after manager.connect. Client likely disconnected.")
            return # Return from outer function
        except Exception as e_connect:
            logger.error(f"WebSocket EP ({prompt_id}): Error during manager.connect/websocket.accept(): {e_connect}", exc_info=True)
            try:
                await websocket.close(code=1011, reason="Server error during connection setup")
            except Exception as close_exc:
                logger.warning(f"WebSocket EP ({prompt_id}): Exception during websocket.close after accept error: {close_exc}", exc_info=True)
            return # Return from outer function
        
        # If manager.connect succeeded, proceed to send initial data and handle messages
        try:
            initial_data_payload = {
                "action": "initial",
                "content": prompt.content,
                "description": prompt.description,
                "tags": prompt.tags,
                "is_composite": prompt.is_composite,
                "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None
            }
            logger.debug(f"WebSocket EP ({prompt_id}): Attempting to send initial data: {initial_data_payload!r}")
            await websocket.send_json(initial_data_payload)
            logger.info(f"WebSocket EP ({prompt_id}): Successfully sent initial data.")
        except WebSocketDisconnect:
            logger.warning(f"WebSocket EP ({prompt_id}): WebSocketDisconnect during initial data send. Client likely disconnected.")
            manager.disconnect(websocket, prompt_id) # Clean up connection
            return # Return from outer function
        except Exception as e_send:
            logger.error(f"WebSocket EP ({prompt_id}): Error sending initial data: {e_send}", exc_info=True)
            manager.disconnect(websocket, prompt_id) # Clean up connection
            return # Return from outer function
        
        # Message handling loop
        logger.debug(f"WebSocket EP ({prompt_id}): Entering message handling loop.")
        while True:
            data = await websocket.receive_json() # This can raise WebSocketDisconnect
            logger.debug(f"WebSocket EP ({prompt_id}): Received data: {data!r}")
            action = data.get("action")
            
            if action == "update":
                content = data.get("content")
                if content is not None:
                    prompt.content = content
                    now = datetime.now(timezone.utc)
                    prompt.updated_at = now
                    logger.debug(f"WebSocket EP ({prompt_id}): Saving updated content.")
                    success = prompt_service.save_prompt(prompt)
                    await websocket.send_json({"action": "update_status", "success": success, "timestamp": now.isoformat()})
                    if success:
                        logger.debug(f"WebSocket EP ({prompt_id}): Broadcasting content update.")
                        await manager.broadcast({"action": "update", "content": content, "timestamp": now.isoformat()}, prompt_id, exclude=websocket)
            
            elif action == "update_metadata":
                description = data.get("description")
                tags = data.get("tags")
                if description is not None:
                    prompt.description = description
                if tags is not None:
                    prompt.tags = tags
                now = datetime.now(timezone.utc)
                prompt.updated_at = now
                logger.debug(f"WebSocket EP ({prompt_id}): Saving updated metadata.")
                success = prompt_service.save_prompt(prompt)
                await websocket.send_json({"action": "update_status", "success": success, "timestamp": now.isoformat()})
                if success:
                    logger.debug(f"WebSocket EP ({prompt_id}): Broadcasting metadata update.")
                    await manager.broadcast({"action": "update_metadata", "description": description, "tags": tags, "timestamp": now.isoformat()}, prompt_id, exclude=websocket)
            
            elif action == "expand":
                content = data.get("content")
                if content is not None:
                    logger.debug(f"WebSocket EP ({prompt_id}): Expanding content.")
                    expanded, dependencies, warnings = prompt_service.expand_inclusions(content, parent_id=prompt.id) # Use prompt.id for consistency
                    await websocket.send_json({"action": "expanded", "content": content, "expanded": expanded, "dependencies": list(dependencies), "warnings": warnings})
            else:
                logger.warning(f"WebSocket EP ({prompt_id}): Unknown action received: {action}")

    except WebSocketDisconnect:
        # This will catch WebSocketDisconnect if it occurs in receive_json() or if thrown by Starlette for client disconnects
        logger.info(f"WebSocket EP ({prompt_id}): Client disconnected (WebSocketDisconnect in outer try).")
    except Exception as e_outer:
        # This is the crucial catch-all for any unexpected errors in the endpoint
        logger.error(f"WebSocket EP ({prompt_id}): UNHANDLED EXCEPTION in websocket_endpoint: {e_outer}", exc_info=True)
        # Do not try to await websocket.close() here if websocket.accept() hasn't been called or failed,
        # as it might raise another error. FastAPI/Starlette will likely handle sending a 500.
    finally:
        # This finally block will always execute, regardless of how the try block exits (return, exception)
        logger.debug(f"WebSocket EP ({prompt_id}): In outer finally block. Disconnecting client.")
        manager.disconnect(websocket, prompt_id) # Ensure cleanup
        logger.debug(f"WebSocket EP ({prompt_id}): Exiting endpoint (from outer finally).")

# The fragment_websocket_endpoint below is legacy and should be removed.
# All WebSocket interactions for prompts (and what were previously fragments)
# should now go through the /ws/prompts/{prompt_id} endpoint above.
