"""
Unified router for the prompt management system.

This module provides a FastAPI router for the prompt management API.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
import json
import os
from pathlib import Path

from prompt_manager.models.unified_prompt import Prompt, PromptType
from prompt_manager.services.prompt_service import PromptService

# Set up logger
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# Dependency to get the prompt service
def get_prompt_service():
    """
    Get the prompt service singleton.
    """
    # Define default directories to scan for prompts
    default_dirs = [
        # Project data directory
        os.path.join(Path(__file__).resolve().parent.parent.parent.parent, "data/prompts"),
        # User config directory
        os.path.expanduser("~/.prompt_manager/prompts")
    ]
    
    # Ensure directories exist
    for directory in default_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Return service
    return PromptService(default_dirs)


# Routes for prompt management

@router.get("", response_model=List[Prompt])
async def list_prompts(
    prompt_type: Optional[PromptType] = None,
    service: PromptService = Depends(get_prompt_service)
):
    """
    List all prompts, optionally filtered by type.
    """
    if prompt_type:
        return [p for p in service.prompts if p.prompt_type == prompt_type]
    return service.prompts


@router.get("/{prompt_id}", response_model=Prompt)
async def get_prompt(
    prompt_id: str,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Get a specific prompt by ID.
    """
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
    return prompt


@router.post("", response_model=Prompt)
async def create_prompt(
    prompt: Prompt,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Create a new prompt.
    """
    try:
        # Use first directory as default for new prompts
        directory = service.directories[0]
        
        # Create the prompt
        created = service.create_prompt(
            id=prompt.id,
            content=prompt.content,
            directory=directory,
            prompt_type=prompt.prompt_type,
            description=prompt.description,
            tags=prompt.tags
        )
        
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{prompt_id}", response_model=Prompt)
async def update_prompt(
    prompt_id: str,
    prompt: Prompt,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Update a prompt by ID.
    """
    try:
        # Check if prompt exists
        existing = service.get_prompt(prompt_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        
        # Update the prompt
        updated = service.update_prompt(
            id=prompt_id,
            content=prompt.content,
            description=prompt.description,
            prompt_type=prompt.prompt_type,
            tags=prompt.tags
        )
        
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Delete a prompt by ID.
    """
    try:
        # Check if prompt exists
        existing = service.get_prompt(prompt_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        
        # Delete the prompt
        service.delete_prompt(prompt_id)
        
        return {"message": f"Prompt {prompt_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{prompt_id}/render", response_model=Dict[str, Any])
async def render_prompt(
    prompt_id: str,
    service: PromptService = Depends(get_prompt_service)
):
    """
    Render a prompt with all inclusions expanded.
    """
    try:
        # Get the prompt
        prompt = service.get_prompt(prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        
        # Render the prompt
        rendered = service.render_prompt(prompt_id)
        
        return {
            "id": prompt_id,
            "original": prompt.content,
            "rendered": rendered,
            "prompt_type": prompt.prompt_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# WebSocket for real-time editing
@router.websocket("/ws/prompts/{prompt_id}")
async def websocket_prompt(
    websocket: WebSocket,
    prompt_id: str,
    service: PromptService = Depends(get_prompt_service)
):
    """
    WebSocket endpoint for real-time prompt editing.
    """
    await websocket.accept()
    
    try:
        # Check if prompt exists
        prompt = service.get_prompt(prompt_id)
        if not prompt:
            await websocket.close(code=1000, reason=f"Prompt {prompt_id} not found")
            return
        
        # Send initial prompt data
        await websocket.send_json({
            "type": "init",
            "data": prompt.dict()
        })
        
        # Main WebSocket loop
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle message
            if message["type"] == "update":
                # Update prompt
                try:
                    updated = service.update_prompt(
                        id=prompt_id,
                        content=message["data"]["content"],
                        description=prompt.description,
                        prompt_type=prompt.prompt_type,
                        tags=prompt.tags
                    )
                    
                    # Send confirmation
                    await websocket.send_json({
                        "type": "update_success",
                        "data": updated.dict()
                    })
                except Exception as e:
                    # Send error
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)}
                    })
            
            elif message["type"] == "render":
                # Render prompt
                try:
                    rendered = service.render_prompt(prompt_id)
                    
                    # Send rendered content
                    await websocket.send_json({
                        "type": "render_result",
                        "data": {"rendered": rendered}
                    })
                except Exception as e:
                    # Send error
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)}
                    })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket for prompt {prompt_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass
