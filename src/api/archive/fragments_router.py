"""
API routes for fragment management.
"""

import os
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.fragment_service import FragmentService
from src.services.prompt_dirs import get_directory_by_path

# Create router
router = APIRouter(prefix="/api/prompts/fragments", tags=["fragments"])

# Get the fragment service singleton
_fragment_service = None
def get_fragment_service():
    """Get the fragment service singleton."""
    global _fragment_service
    if _fragment_service is None:
        _fragment_service = FragmentService(auto_load=True)
    return _fragment_service

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
@router.get("/", response_model=List[Dict])
async def get_all_fragments():
    """Get all fragments."""
    fragment_service = get_fragment_service()
    fragments = list(fragment_service.fragments.values())
    result = []
    
    for fragment in fragments:
        fragment_dict = fragment.dict()
        fragment_dict["directory_name"] = get_directory_name(fragment_dict["directory"])
        result.append(fragment_dict)
    
    return result

@router.get("/{fragment_id}", response_model=Dict)
async def get_fragment_by_id(fragment_id: str):
    """Get a specific fragment by ID."""
    fragment_service = get_fragment_service()
    fragment = fragment_service.get_fragment(fragment_id)
    
    if not fragment:
        raise HTTPException(status_code=404, detail=f"Fragment '{fragment_id}' not found")
    
    fragment_dict = fragment.dict()
    fragment_dict["directory_name"] = get_directory_name(fragment_dict["directory"])
    
    return fragment_dict

@router.post("/", response_model=Dict)
async def create_new_fragment(fragment: FragmentCreate):
    """Create a new fragment."""
    fragment_service = get_fragment_service()
    
    # Check if the fragment ID already exists
    if fragment_service.get_fragment(fragment.id):
        raise HTTPException(status_code=400, detail=f"Fragment with ID '{fragment.id}' already exists")
    
    # Create new fragment
    try:
        new_fragment = fragment_service.create_fragment(
            id=fragment.id,
            content=fragment.content,
            directory=fragment.directory,
            description=fragment.description,
            tags=fragment.tags or []
        )
        
        fragment_dict = new_fragment.dict()
        fragment_dict["directory_name"] = get_directory_name(fragment_dict["directory"])
        
        return fragment_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating fragment: {str(e)}")

@router.put("/{fragment_id}", response_model=Dict)
async def update_existing_fragment(fragment_id: str, update_data: FragmentUpdate):
    """Update an existing fragment."""
    fragment_service = get_fragment_service()
    fragment = fragment_service.get_fragment(fragment_id)
    
    if not fragment:
        raise HTTPException(status_code=404, detail=f"Fragment '{fragment_id}' not found")
    
    # Update fields
    if update_data.content is not None:
        fragment.content = update_data.content
    
    if update_data.description is not None:
        fragment.description = update_data.description
    
    if update_data.tags is not None:
        fragment.tags = update_data.tags
    
    # Save the updated fragment
    try:
        fragment_service.save_fragment(fragment)
        
        fragment_dict = fragment.dict()
        fragment_dict["directory_name"] = get_directory_name(fragment_dict["directory"])
        
        return fragment_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating fragment: {str(e)}")

@router.delete("/{fragment_id}", response_model=Dict)
async def delete_existing_fragment(fragment_id: str):
    """Delete an existing fragment."""
    fragment_service = get_fragment_service()
    
    if not fragment_service.get_fragment(fragment_id):
        raise HTTPException(status_code=404, detail=f"Fragment '{fragment_id}' not found")
    
    # Delete the fragment
    try:
        result = fragment_service.delete_fragment(fragment_id)
        return {"success": result, "id": fragment_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting fragment: {str(e)}")

@router.post("/reload", response_model=Dict)
async def reload_fragments():
    """Reload all fragments from all directories."""
    fragment_service = get_fragment_service()
    
    try:
        # Clear fragments and reload
        fragment_service.fragments = {}
        count = fragment_service.load_all_fragments()
        
        return {
            "success": True,
            "count": count,
            "message": f"Successfully reloaded {count} fragments"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading fragments: {str(e)}")

@router.post("/directories/{directory_path:path}/reload", response_model=Dict)
async def reload_directory(directory_path: str):
    """Reload fragments from a specific directory."""
    fragment_service = get_fragment_service()
    
    # Find the directory
    directory_exists = False
    for dir_info in fragment_service.directories:
        if dir_info.path == directory_path:
            directory_exists = True
            break
    
    if not directory_exists:
        # Try to add the directory if it exists on disk
        if os.path.isdir(directory_path):
            fragment_service.add_directory(directory_path)
            directory_exists = True
        else:
            raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found")
    
    try:
        # Remove fragments from this directory
        fragments_to_remove = [f_id for f_id, f in fragment_service.fragments.items() if f.directory == directory_path]
        for fragment_id in fragments_to_remove:
            del fragment_service.fragments[fragment_id]
        
        # Reload fragments from the directory
        count = fragment_service.load_fragments_from_directory(directory_path)
        
        return {
            "success": True,
            "count": count,
            "message": f"Successfully reloaded {count} fragments from directory: {directory_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading directory: {str(e)}")
