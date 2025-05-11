"""
API routes for prompt management.
"""

import os
import shutil
from typing import List, Dict, Optional, Union
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.default_prompts import create_default_prompt, create_all_default_prompts, check_default_prompts_exist, DEFAULT_PROMPTS

# Create router
router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# Mock data for development
mock_prompts = [
    {
        "id": "architect_role",
        "description": "System prompt for the Architect AI",
        "prompt_type": "system",
        "tags": ["architect", "system", "role"],
        "directory": "/home/jem/development/coordinator/data/prompts",
        "updated_at": "2025-05-09T12:00:00Z",
        "content": "# Architect Role\n\nYou are the Architect AI..."
    },
    {
        "id": "worker_role",
        "description": "System prompt for Worker AIs",
        "prompt_type": "system",
        "tags": ["worker", "system", "role"],
        "directory": "/home/jem/development/coordinator/data/prompts",
        "updated_at": "2025-05-09T12:00:00Z",
        "content": "# Worker Role\n\nYou are a specialized Worker AI..."
    },
    {
        "id": "code_worker_role",
        "description": "System prompt for Code Worker AIs",
        "prompt_type": "system",
        "tags": ["worker", "system", "role", "code"],
        "directory": "/home/jem/development/coordinator/data/prompts",
        "updated_at": "2025-05-09T12:00:00Z",
        "content": "# Code Worker Role\n\nYou are a specialized Code Worker AI..."
    }
]

mock_directories = [
    {
        "path": "/home/jem/development/coordinator/data/prompts",
        "name": "Default Prompts",
        "description": "Default prompt directory",
        "enabled": True
    }
]

# Models
class PromptCreate(BaseModel):
    id: str
    content: str
    directory: str
    prompt_type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class PromptUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    prompt_type: Optional[str] = None

class DirectoryCreate(BaseModel):
    path: str
    name: Optional[str] = None
    description: Optional[str] = None

class DefaultPromptsCreate(BaseModel):
    directory: str
    prompt_ids: Optional[List[str]] = None


# Routes

@router.get("/all", response_model=List[Dict])
async def get_all_prompts():
    """Get all prompts."""
    # For development, use mock data
    return mock_prompts


@router.get("/{prompt_id}", response_model=Dict)
async def get_prompt_by_id(prompt_id: str):
    """Get a specific prompt by ID."""
    # For development, use mock data
    for prompt in mock_prompts:
        if prompt["id"] == prompt_id:
            return prompt
    
    raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")


@router.post("/", response_model=Dict)
async def create_new_prompt(prompt: PromptCreate):
    """Create a new prompt."""
    # Check if the prompt ID already exists
    for existing_prompt in mock_prompts:
        if existing_prompt["id"] == prompt.id:
            raise HTTPException(status_code=400, detail=f"Prompt with ID '{prompt.id}' already exists")
    
    # Create new prompt
    new_prompt = {
        "id": prompt.id,
        "description": prompt.description or "",
        "prompt_type": prompt.prompt_type,
        "tags": prompt.tags or [],
        "directory": prompt.directory,
        "updated_at": "2025-05-09T12:00:00Z",
        "content": prompt.content
    }
    
    mock_prompts.append(new_prompt)
    return new_prompt


@router.put("/{prompt_id}", response_model=Dict)
async def update_existing_prompt(prompt_id: str, update_data: PromptUpdate):
    """Update an existing prompt."""
    # Find the prompt
    for prompt in mock_prompts:
        if prompt["id"] == prompt_id:
            # Update fields
            if update_data.content is not None:
                prompt["content"] = update_data.content
            
            if update_data.description is not None:
                prompt["description"] = update_data.description
            
            if update_data.tags is not None:
                prompt["tags"] = update_data.tags
            
            if update_data.prompt_type is not None:
                prompt["prompt_type"] = update_data.prompt_type
            
            prompt["updated_at"] = "2025-05-09T12:30:00Z"
            
            return prompt
    
    raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")


@router.delete("/{prompt_id}", response_model=Dict)
async def delete_existing_prompt(prompt_id: str):
    """Delete an existing prompt."""
    # Find the prompt
    for i, prompt in enumerate(mock_prompts):
        if prompt["id"] == prompt_id:
            # Remove the prompt
            deleted_prompt = mock_prompts.pop(i)
            return {"success": True, "id": prompt_id}
    
    raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")


@router.get("/directories/all", response_model=List[Dict])
async def get_all_directories():
    """Get all prompt directories."""
    # For development, use mock data
    return mock_directories


@router.post("/directories", response_model=Dict)
async def add_directory(directory: DirectoryCreate):
    """Add a new prompt directory."""
    # Check if directory already exists
    for existing_dir in mock_directories:
        if existing_dir["path"] == directory.path:
            raise HTTPException(status_code=400, detail=f"Directory '{directory.path}' already exists")
    
    # Create new directory
    new_directory = {
        "path": directory.path,
        "name": directory.name or os.path.basename(directory.path),
        "description": directory.description or "",
        "enabled": True
    }
    
    mock_directories.append(new_directory)
    return new_directory


@router.delete("/directories/{directory_path:path}", response_model=Dict)
async def remove_directory(directory_path: str):
    """Remove a prompt directory."""
    # Find the directory
    for i, directory in enumerate(mock_directories):
        if directory["path"] == directory_path:
            # Remove the directory
            deleted_directory = mock_directories.pop(i)
            return {"success": True, "path": directory_path}
    
    raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found")


@router.post("/default-prompts", response_model=Dict)
async def create_default_prompts(data: DefaultPromptsCreate):
    """Create default prompts in the specified directory."""
    # Check if directory exists
    directory_exists = False
    for dir_info in mock_directories:
        if dir_info["path"] == data.directory:
            directory_exists = True
            break
    
    if not directory_exists:
        raise HTTPException(status_code=404, detail=f"Directory '{data.directory}' not found")
    
    # Create prompts
    created_prompts = []
    prompt_ids = data.prompt_ids or list(DEFAULT_PROMPTS.keys())
    
    for prompt_id in prompt_ids:
        if prompt_id not in DEFAULT_PROMPTS:
            continue
        
        # Check if prompt already exists
        exists = False
        for prompt in mock_prompts:
            if prompt["id"] == prompt_id:
                exists = True
                break
        
        if not exists:
            # Create prompt
            prompt_data = DEFAULT_PROMPTS[prompt_id].copy()
            prompt_data["directory"] = data.directory
            prompt_data["updated_at"] = "2025-05-09T12:00:00Z"
            
            mock_prompts.append(prompt_data)
            created_prompts.append(prompt_id)
    
    return {
        "success": True,
        "directory": data.directory,
        "created_prompts": created_prompts
    }
