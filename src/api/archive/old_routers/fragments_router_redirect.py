"""
API routes for fragment management - redirected to prompts.

This module provides a compatibility layer that redirects fragment API calls
to the prompt API.
"""

import os
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.api.router import get_prompt_service, PromptCreate, PromptUpdate

# Create router with the same prefix as the original fragments router
router = APIRouter(prefix="/api/prompts/fragments", tags=["fragments"])

# Models
class FragmentCreate(BaseModel):
    id: str
    content: str
    directory: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class FragmentUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


# Routes that redirect to the prompt API
@router.get("/", response_model=List[Dict])
async def get_all_fragments(prompt_service=Depends(get_prompt_service)):
    """Get all prompts (formerly fragments)."""
    prompts = list(prompt_service.prompts.values())
    result = []
    
    for prompt in prompts:
        prompt_dict = prompt.dict()
        # Add directory_name for compatibility
        prompt_dict["directory_name"] = os.path.basename(prompt_dict["directory"])
        result.append(prompt_dict)
    
    return result

@router.get("/{fragment_id}", response_model=Dict)
async def get_fragment_by_id(fragment_id: str, prompt_service=Depends(get_prompt_service)):
    """Get a specific prompt by ID (formerly fragment)."""
    prompt = prompt_service.get_prompt(fragment_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{fragment_id}' not found")
    
    prompt_dict = prompt.dict()
    # Add directory_name for compatibility
    prompt_dict["directory_name"] = os.path.basename(prompt_dict["directory"])
    
    return prompt_dict

@router.post("/", response_model=Dict)
async def create_new_fragment(fragment: FragmentCreate, prompt_service=Depends(get_prompt_service)):
    """Create a new prompt (formerly fragment)."""
    # Check if the prompt ID already exists
    if prompt_service.get_prompt(fragment.id):
        raise HTTPException(status_code=400, detail=f"Prompt with ID '{fragment.id}' already exists")
    
    # Convert to PromptCreate and use the prompt service
    prompt_create = PromptCreate(
        id=fragment.id,
        content=fragment.content,
        directory=fragment.directory,
        description=fragment.description,
        tags=fragment.tags or []
    )
    
    # Create new prompt
    try:
        new_prompt = prompt_service.create_prompt(
            id=prompt_create.id,
            content=prompt_create.content,
            directory=prompt_create.directory,
            description=prompt_create.description,
            tags=prompt_create.tags
        )
        
        prompt_dict = new_prompt.dict()
        prompt_dict["directory_name"] = os.path.basename(prompt_dict["directory"])
        
        return prompt_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating prompt: {str(e)}")

@router.put("/{fragment_id}", response_model=Dict)
async def update_existing_fragment(fragment_id: str, update_data: FragmentUpdate, prompt_service=Depends(get_prompt_service)):
    """Update an existing prompt (formerly fragment)."""
    prompt = prompt_service.get_prompt(fragment_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{fragment_id}' not found")
    
    # Update fields
    if update_data.content is not None:
        prompt.content = update_data.content
    
    if update_data.description is not None:
        prompt.description = update_data.description
    
    if update_data.tags is not None:
        prompt.tags = update_data.tags
    
    # Save the updated prompt
    try:
        prompt_service.save_prompt(prompt)
        
        prompt_dict = prompt.dict()
        prompt_dict["directory_name"] = os.path.basename(prompt_dict["directory"])
        
        return prompt_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prompt: {str(e)}")

@router.delete("/{fragment_id}", response_model=Dict)
async def delete_existing_fragment(fragment_id: str, prompt_service=Depends(get_prompt_service)):
    """Delete an existing prompt (formerly fragment)."""
    if not prompt_service.get_prompt(fragment_id):
        raise HTTPException(status_code=404, detail=f"Prompt '{fragment_id}' not found")
    
    # Delete the prompt
    try:
        result = prompt_service.delete_prompt(fragment_id)
        return {"success": result, "id": fragment_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting prompt: {str(e)}")

@router.post("/expand", response_model=Dict)
async def expand_inclusions(request: Dict, prompt_service=Depends(get_prompt_service)):
    """Expand inclusions in content."""
    content = request.get("content", "")
    
    expanded, dependencies, warnings = prompt_service.expand_inclusions(content)
    
    return {
        "expanded": expanded,
        "dependencies": list(dependencies),
        "warnings": warnings
    }

@router.post("/reload", response_model=Dict)
async def reload_fragments(prompt_service=Depends(get_prompt_service)):
    """Reload all prompts (formerly fragments)."""
    try:
        # Clear prompts and reload
        prompt_service.prompts = {}
        count = prompt_service.load_all_prompts()
        
        return {
            "success": True,
            "count": count,
            "message": f"Successfully reloaded {count} prompts"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading prompts: {str(e)}")

@router.post("/directories/{directory_path:path}/reload", response_model=Dict)
async def reload_directory(directory_path: str, prompt_service=Depends(get_prompt_service)):
    """Reload prompts from a specific directory."""
    # Find the directory
    directory_exists = False
    for dir_path in prompt_service.directories:
        if dir_path == directory_path:
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
