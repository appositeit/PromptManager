"""
API routes for prompt management.
"""

import os
import shutil
from typing import List, Dict, Optional, Union
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.services.default_prompts import create_default_prompt, create_all_default_prompts, check_default_prompts_exist, DEFAULT_PROMPTS
from src.services.prompt_dirs import get_directory_by_path, get_default_directory
from src.services.prompt_service import PromptService

# Create router
router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# Get the prompt service singleton
_prompt_service = None
def get_prompt_service():
    """Get the prompt service singleton."""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService(auto_load=True)
    return _prompt_service

# Models
class PromptCreate(BaseModel):
    id: str
    content: Optional[str] = ""
    directory: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class PromptUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class DirectoryCreate(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None

class DirectoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None

class DirectoryStatusToggle(BaseModel):
    enabled: Optional[bool] = None

class DefaultPromptsCreate(BaseModel):
    directory: str
    prompt_ids: Optional[List[str]] = None


# Helper functions
def get_directory_name(directory_path: str) -> str:
    """Get directory name from path."""
    # Try to get from directory service if available
    dir_info = get_directory_by_path(directory_path)
    if dir_info:
        return dir_info.get("name", os.path.basename(directory_path))
    
    # Default to base name of path
    return os.path.basename(directory_path)


# Routes

@router.get("/all", response_model=List[Dict])
async def get_all_prompts():
    """Get all prompts."""
    prompt_service = get_prompt_service()
    
    # If prompts are empty, force a reload
    if not prompt_service.prompts:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("No prompts found in service - forcing reload")
        count = prompt_service.load_all_prompts()
        logger.info(f"Reloaded {count} prompts")
    
    prompts = list(prompt_service.prompts.values())
    result = []
    
    for prompt in prompts:
        prompt_dict = prompt.dict()
        prompt_dict["directory_name"] = get_directory_name(prompt_dict["directory"])
        # Ensure the unique_id is included in the response
        if not prompt_dict.get("unique_id"):
            prompt_dict["unique_id"] = prompt.get_unique_id
        result.append(prompt_dict)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Returning {len(result)} prompts")
    
    return result


@router.get("/{prompt_id}", response_model=Dict)
async def get_prompt_by_id(prompt_id: str, directory: Optional[str] = None):
    """
    Get a specific prompt by ID.
    
    If multiple prompts have the same ID, you can specify a directory to disambiguate.
    """
    prompt_service = get_prompt_service()
    prompt = prompt_service.get_prompt(prompt_id, directory)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
    
    prompt_dict = prompt.dict()
    prompt_dict["directory_name"] = get_directory_name(prompt_dict["directory"])
    
    return prompt_dict


@router.post("/", response_model=Dict)
async def create_new_prompt(prompt: PromptCreate):
    """Create a new prompt."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating prompt with data: {prompt}")
    
    prompt_service = get_prompt_service()
    
    # Check if the prompt ID already exists
    if prompt_service.get_prompt(prompt.id):
        logger.warning(f"Prompt ID already exists: {prompt.id}")
        raise HTTPException(status_code=400, detail=f"Prompt with ID '{prompt.id}' already exists")
    
    # Print the incoming data for debugging
    import json
    logger.info(f"Prompt data: {json.dumps(prompt.dict(), indent=2)}")
    
    # Validate directory
    if not prompt.directory:
        logger.error("Directory is missing")
        raise HTTPException(status_code=400, detail="Directory is required")
    
    # No longer need to validate prompt_type
    
    # Create new prompt
    try:
        logger.info(f"Creating prompt with: id={prompt.id}, directory={prompt.directory}")
        
        new_prompt = prompt_service.create_prompt(
            id=prompt.id,
            content=prompt.content or "",
            directory=prompt.directory,

            description=prompt.description,
            tags=prompt.tags or []
        )
        
        prompt_dict = new_prompt.dict()
        prompt_dict["directory_name"] = get_directory_name(prompt_dict["directory"])
        
        logger.info(f"Successfully created prompt: {prompt.id}")
        return prompt_dict
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating prompt: {str(e)}")


@router.put("/{prompt_id}", response_model=Dict)
async def update_existing_prompt(prompt_id: str, update_data: PromptUpdate):
    """Update an existing prompt."""
    prompt_service = get_prompt_service()
    prompt = prompt_service.get_prompt(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
    
    # Update fields
    if update_data.content is not None:
        prompt.content = update_data.content
    
    if update_data.description is not None:
        prompt.description = update_data.description
    
    if update_data.tags is not None:
        prompt.tags = update_data.tags
    
    # Removed prompt_type update
    
    # Save the updated prompt
    try:
        prompt_service.save_prompt(prompt)
        
        prompt_dict = prompt.dict()
        prompt_dict["directory_name"] = get_directory_name(prompt_dict["directory"])
        
        return prompt_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prompt: {str(e)}")


@router.delete("/{prompt_id}", response_model=Dict)
async def delete_existing_prompt(prompt_id: str):
    """Delete an existing prompt."""
    prompt_service = get_prompt_service()
    
    if not prompt_service.get_prompt(prompt_id):
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
    
    # Delete the prompt
    try:
        result = prompt_service.delete_prompt(prompt_id)
        return {"success": result, "id": prompt_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting prompt: {str(e)}")


@router.get("/directories/all", response_model=List[Dict])
async def get_all_directories():
    """Get all prompt directories."""
    prompt_service = get_prompt_service()
    return [dir.dict() for dir in prompt_service.directories]


@router.post("/directories", response_model=Dict)
async def add_directory(directory: DirectoryCreate):
    """Add a new prompt directory."""
    prompt_service = get_prompt_service()
    
    # Check if directory already exists
    for existing_dir in prompt_service.directories:
        if existing_dir.path == directory.path:
            raise HTTPException(status_code=400, detail=f"Directory '{directory.path}' already exists")
    
    # Create new directory
    try:
        result = prompt_service.add_directory(
            path=directory.path,
            name=directory.name,
            description=directory.description
        )
        
        if not result:
            raise HTTPException(status_code=400, detail=f"Could not add directory '{directory.path}'")
        
        # Get the newly added directory
        for dir_info in prompt_service.directories:
            if dir_info.path == directory.path:
                return dir_info.dict()
        
        # Fallback in case we can't find the directory
        return {
            "path": directory.path,
            "name": directory.name or os.path.basename(directory.path),
            "description": directory.description or "",
            "enabled": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding directory: {str(e)}")


@router.put("/directories/{directory_path:path}", response_model=Dict)
async def update_directory(directory_path: str, data: DirectoryUpdate):
    """Update a directory's properties."""
    prompt_service = get_prompt_service()
    
    # Find the directory
    directory_idx = None
    for i, dir_info in enumerate(prompt_service.directories):
        if dir_info.path == directory_path:
            directory_idx = i
            break
    
    if directory_idx is None:
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found")
    
    # Update the directory properties
    try:
        # Update allowed fields
        if data.name is not None:
            prompt_service.directories[directory_idx].name = data.name
        
        if data.description is not None:
            prompt_service.directories[directory_idx].description = data.description
        
        if data.enabled is not None:
            prompt_service.directories[directory_idx].enabled = data.enabled
        
        # Save the configuration
        prompt_service._save_directory_config()
        
        return prompt_service.directories[directory_idx].dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating directory: {str(e)}")


@router.post("/directories/{directory_path:path}/toggle", response_model=Dict)
async def toggle_directory_status(directory_path: str, data: DirectoryStatusToggle):
    """Toggle a directory's enabled status."""
    prompt_service = get_prompt_service()
    
    # Find the directory
    directory_idx = None
    for i, dir_info in enumerate(prompt_service.directories):
        if dir_info.path == directory_path:
            directory_idx = i
            break
    
    if directory_idx is None:
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found")
    
    # Update the directory status
    try:
        # Get the enabled value, default to toggle the current value if not provided
        enabled = data.enabled
        if enabled is None:
            enabled = not prompt_service.directories[directory_idx].enabled
        
        # Update the directory status
        prompt_service.directories[directory_idx].enabled = enabled
        
        # Save the configuration
        prompt_service._save_directory_config()
        
        # Reload prompts if the directory was enabled
        if enabled:
            # Remove prompts from this directory first
            prompts_to_remove = [p_id for p_id, p in prompt_service.prompts.items() 
                                  if p.directory == directory_path]
            for prompt_id in prompts_to_remove:
                del prompt_service.prompts[prompt_id]
            
            # Load prompts from the directory
            count = prompt_service.load_prompts_from_directory(directory_path)
        else:
            # If disabled, remove prompts from this directory
            prompts_to_remove = [p_id for p_id, p in prompt_service.prompts.items() 
                                  if p.directory == directory_path]
            for prompt_id in prompts_to_remove:
                del prompt_service.prompts[prompt_id]
            count = len(prompts_to_remove)
        
        return {
            "success": True,
            "path": directory_path,
            "enabled": enabled,
            "affected_prompts": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling directory status: {str(e)}")


@router.delete("/directories/{directory_path:path}", response_model=Dict)
async def remove_directory(directory_path: str):
    """Remove a prompt directory."""
    prompt_service = get_prompt_service()
    
    # Find the directory
    directory_exists = False
    for dir_info in prompt_service.directories:
        if dir_info.path == directory_path:
            directory_exists = True
            break
    
    if not directory_exists:
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found")
    
    # Remove the directory
    try:
        result = prompt_service.remove_directory(directory_path)
        return {"success": result, "path": directory_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing directory: {str(e)}")


@router.get("/debug/routes", response_model=Dict)
async def debug_routes():
    """Debug endpoint to list all routes."""
    from fastapi import FastAPI
    from src.server import app
    
    # Get all routes
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", str(route)),
            "name": getattr(route, "name", None),
            "methods": getattr(route, "methods", None),
            "type": str(type(route))
        })
    
    return {
        "routes": routes,
        "count": len(routes)
    }

@router.post("/reload", response_model=Dict)
async def reload_prompts():
    """Reload all prompts from all directories."""
    prompt_service = get_prompt_service()
    
    try:
        # Clear prompts and reload
        prompt_service.prompts = {}
        count = prompt_service.load_all_prompts()
        
        return {
            "success": True,
            "count": count,
            "message": f"Successfully reloaded {count} prompts from {len(prompt_service.directories)} directories"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading prompts: {str(e)}")


# Expansion endpoint for API fallback
class ExpandRequest(BaseModel):
    content: str
    prompt_id: Optional[str] = None

@router.post("/expand", response_model=Dict)
async def expand_content(request: ExpandRequest):
    """Expand inclusions in prompt content."""
    prompt_service = get_prompt_service()
    
    try:
        expanded, dependencies, warnings = prompt_service.expand_inclusions(
            request.content, 
            root_id=request.prompt_id
        )
        
        return {
            "content": request.content,
            "expanded": expanded,
            "dependencies": list(dependencies),
            "warnings": warnings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error expanding content: {str(e)}")


@router.post("/directories/{directory_path:path}/reload", response_model=Dict)
async def reload_directory(directory_path: str):
    """Reload prompts from a specific directory."""
    prompt_service = get_prompt_service()
    
    # Find the directory
    directory_exists = False
    for dir_info in prompt_service.directories:
        if dir_info.path == directory_path:
            directory_exists = True
            break
    
    if not directory_exists:
        # Try to add the directory if it exists on disk
        if os.path.isdir(directory_path):
            prompt_service.add_directory(directory_path)
            directory_exists = True
        else:
            raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found")
    
    try:
        # Remove prompts from this directory
        prompts_to_remove = [p_id for p_id, p in prompt_service.prompts.items() if p.directory == directory_path]
        for prompt_id in prompts_to_remove:
            del prompt_service.prompts[prompt_id]
        
        # Reload prompts from the directory
        count = prompt_service.load_prompts_from_directory(directory_path)
        
        return {
            "success": True,
            "count": count,
            "message": f"Successfully reloaded {count} prompts from directory: {directory_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading directory: {str(e)}")
