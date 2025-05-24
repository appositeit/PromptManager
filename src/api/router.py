"""
API routes for prompt management.
"""

import os
import sys
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger
from datetime import datetime, timezone

from src.models.prompt import PromptDirectory

# Add parent directory to sys.path to make imports work from anywhere
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import our services with better path handling
try:
    # Try absolute imports
    from src.services.prompt_dirs import get_directory_by_path
    from src.services.prompt_service import PromptService as PromptServiceClass
    logger.debug("Successfully imported services using absolute paths (expected for src layout).")
except ImportError:
    try:
        # Try with src prefix
        from src.services.prompt_dirs import get_directory_by_path
        from src.services.prompt_service import PromptService as PromptServiceClass
        logger.debug("Successfully imported services using src prefix.")
    except ImportError as e_inner:
        # Try relative imports as last resort
        from ..services.prompt_dirs import get_directory_by_path
        from ..services.prompt_service import PromptService as PromptServiceClass
        print("Using relative imports in router.py for prompt_dirs and PromptService")

# Import the new FilesystemService

# Placeholder dependency function - this will be overridden by the main app
async def get_prompt_service_dependency() -> PromptServiceClass:
    raise NotImplementedError("PromptService dependency not configured. This should be overridden by the main FastAPI app.")

# Create router
router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# Models
class PromptCreate(BaseModel):
    name: str  # Changed from 'id' to 'name'
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

# Model for prompt expansion request
class PromptExpandRequest(BaseModel):
    prompt_id: str
    directory: Optional[str] = None # To disambiguate if prompts have same simple ID in different dirs

# Model for prompt expansion response
class PromptExpandResponse(BaseModel):
    prompt_id: str
    original_content: str
    expanded_content: str
    dependencies: List[str]
    warnings: List[str]

# Model for prompt rename request
class PromptRenameRequest(BaseModel):
    old_id: str  # Can be ID or name
    new_name: str  # New display name (not full ID)
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

# Filesystem completion models
class FilesystemPathRequest(BaseModel):
    partial_path: str

class FilesystemCompletionResponse(BaseModel):
    completed_path: str
    suggestions: List[str]
    is_directory: bool

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
async def get_all_prompts(prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Get all prompts (metadata only)."""
    prompts = list(prompt_service.prompts.values())
    result = []
    
    for prompt in prompts:
        prompt_dict = {
            "id": prompt.id,
            "name": getattr(prompt, 'name', prompt.id),
            "description": prompt.description,
            "tags": prompt.tags,
            "directory": prompt.directory,
            "directory_name": get_directory_name(prompt.directory),
            "unique_id": prompt.unique_id,
            "content": prompt.content,
            "updated_at": prompt.updated_at.isoformat() if getattr(prompt, 'updated_at', None) else None,
            "created_at": prompt.created_at.isoformat() if getattr(prompt, 'created_at', None) else None,
        }
        result.append(prompt_dict)
    
    logger.info(f"Returning {len(result)} prompts (metadata only)") # Updated log message
    
    return result

@router.get("/search_suggestions", response_model=List[Dict])
async def get_prompt_suggestions(
    query: Optional[str] = "",
    exclude: Optional[str] = None,
    prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)
):
    """Get prompt suggestions for autocompletion based on a query string."""
    logger.info(f"Searching suggestions for query: '{query}', excluding: '{exclude}'")
    try:
        suggestions = prompt_service.search_prompt_suggestions(query, exclude)
        return suggestions 
    except Exception as e:
        logger.opt(exception=True).error(f"Error searching prompt suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while searching prompt suggestions")

# Directory routes - MUST come before the catch-all {prompt_id:path} route
@router.get("/directories/all", response_model=List[Dict])
async def get_all_directories(prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Get all configured prompt directories."""
    return [d.dict() for d in prompt_service.directories]

@router.post("/directories", response_model=Dict)
async def add_directory(directory: DirectoryCreate, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Add a new prompt directory."""
    logger.info(f"Adding directory: {directory.path}")
    try:
        # Normalize path before adding. PromptService's add_directory also normalizes.
        # Consider if client-side normalization or a utility function is better before this point.
        normalized_path = os.path.normpath(directory.path)
        
        # Check if directory already exists by normalized path
        for existing_dir in prompt_service.directories:
            if existing_dir.path == normalized_path:
                logger.warning(f"Directory with normalized path '{normalized_path}' already exists.")
                raise HTTPException(status_code=400, detail=f"Directory '{normalized_path}' already exists.")

        success = prompt_service.add_directory(
            path=directory.path, # Let PromptService handle its internal normalization fully
            name=directory.name,
            description=directory.description
        )
        if not success:
            # This could be due to path not found or other issues in add_directory
            logger.error(f"Failed to add directory: {directory.path}")
            raise HTTPException(status_code=400, detail="Could not add directory. Ensure path is valid and accessible.")
        
        # Find the added directory to return its full data
        # add_directory in PromptService now returns bool, so we need to retrieve it.
        # This assumes PromptService's internal normalization matches what we'd expect to find.
        added_dir_obj = None
        for d_obj in prompt_service.directories:
            if d_obj.path == prompt_service._normalize_path(directory.path):
                 added_dir_obj = d_obj
                 break
        
        if not added_dir_obj:
            # Should not happen if add_directory succeeded and normalization is consistent
            logger.error(f"Could not find directory '{directory.path}' after adding it.")
            raise HTTPException(status_code=500, detail="Error retrieving directory after adding.")
            
        return added_dir_obj.dict()

    except HTTPException: # Re-raise HTTP exceptions directly
        raise
    except Exception as e:
        logger.opt(exception=True).error(f"Error adding directory {directory.path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error adding directory.")

@router.put("/directories/{directory_path:path}", response_model=Dict)
async def update_directory(directory_path: str, data: DirectoryUpdate, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Update an existing prompt directory's name, description, or enabled status."""
    # Normalize the input path for comparison
    normalized_input_path = os.path.normpath(directory_path)
    logger.info(f"Updating directory: Normalized path '{normalized_input_path}' with data: {data.dict(exclude_none=True)}")

    found_dir: Optional[PromptDirectory] = None
    for d in prompt_service.directories:
        if os.path.normpath(d.path) == normalized_input_path:
            found_dir = d
            break
            
    if not found_dir:
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")

    updated = False
    reload_needed = False # Flag to check if prompts need reloading due to path or enabled change

    if data.name is not None and found_dir.name != data.name:
        logger.info(f"Updating directory name from '{found_dir.name}' to '{data.name}'")
        found_dir.name = data.name
        updated = True
        
    if data.description is not None and found_dir.description != data.description:
        logger.info(f"Updating directory description from '{found_dir.description}' to '{data.description}'")
        found_dir.description = data.description
        updated = True
        
    if data.enabled is not None and found_dir.enabled != data.enabled:
        logger.info(f"Updating directory enabled status from '{found_dir.enabled}' to '{data.enabled}'")
        found_dir.enabled = data.enabled
        updated = True
        reload_needed = True # Prompts should be reloaded if enabled status changes

    if updated:
        prompt_service._save_directory_config() # Save changes to the config file
        logger.info(f"Directory '{found_dir.path}' updated in config.")
        
        if reload_needed and found_dir.enabled:
            logger.info(f"Directory '{found_dir.path}' was enabled or re-enabled, reloading its prompts.")
            # Pass the PromptDirectory object directly
            count = prompt_service.load_prompts_from_directory(found_dir)
            logger.info(f"Reloaded {count} prompts from directory: {found_dir.path}")
        elif reload_needed and not found_dir.enabled:
            logger.info(f"Directory '{found_dir.path}' was disabled. Prompts from this directory will be effectively unavailable until re-enabled.")
            # Optionally, clear prompts from this directory from the service's cache
            # For now, they just won't be reloaded or actively served if get_prompt filters by enabled dirs.
            # prompt_service.clear_prompts_from_directory(found_dir.path) # Example of a method to implement

    return found_dir.dict()

@router.post("/directories/{directory_path:path}/toggle", response_model=Dict)
async def toggle_directory_status(directory_path: str, data: DirectoryStatusToggle, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Toggle the enabled status of a directory."""
    normalized_path_to_find = prompt_service._normalize_path(directory_path)
    logger.info(f"Toggling status for directory: Original='{directory_path}', Normalized='{normalized_path_to_find}' to enabled={data.enabled}")

    dir_to_toggle = None
    for i, d_obj in enumerate(prompt_service.directories):
        if d_obj.path == normalized_path_to_find:
            dir_to_toggle = d_obj
            break
    
    if not dir_to_toggle:
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found.")

    if data.enabled is not None and dir_to_toggle.enabled != data.enabled:
        dir_to_toggle.enabled = data.enabled
        
        if dir_to_toggle.enabled:
            logger.info(f"Directory '{dir_to_toggle.path}' re-enabled, reloading its prompts.")
            count = prompt_service.load_prompts_from_directory(dir_to_toggle)
            logger.info(f"Reloaded {count} prompts from '{dir_to_toggle.path}'.")
        else:
            logger.info(f"Directory '{dir_to_toggle.path}' disabled.")

        prompt_service._save_directory_config()
        logger.info(f"Directory config saved after toggling status for '{dir_to_toggle.path}'.")

    return dir_to_toggle.dict()

@router.delete("/directories/{directory_path:path}", response_model=Dict)
async def delete_directory(directory_path: str, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Delete a directory from the prompt service."""
    logger.info(f"Deleting directory: {directory_path}")
    
    normalized_path = prompt_service._normalize_path(directory_path)
    success = prompt_service.remove_directory(normalized_path)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Directory '{directory_path}' not found or could not be deleted")
        
    return {"message": f"Directory '{directory_path}' deleted successfully"}

# Other specific routes (reload, expand, rename, filesystem/complete_path)
@router.post("/reload", response_model=Dict)
async def reload_all_prompts_endpoint(prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Reload all prompts from all configured directories."""
    logger.info("API endpoint /reload called. Reloading all prompts.")
    try:
        count = prompt_service.load_all_prompts()
        return {"message": f"Successfully reloaded {count} prompts from all directories.", "count": count}
    except Exception as e:
        logger.opt(exception=True).error(f"Error during /reload endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error while reloading prompts: {str(e)}")

@router.post("/expand", response_model=PromptExpandResponse)
async def expand_prompt_content(
    request_data: PromptExpandRequest,
    prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)
):
    """Expand a prompt's content by recursively including dependencies."""
    logger.info(f"Expanding prompt: {request_data.prompt_id}")
    try:
        prompt = prompt_service.get_prompt(request_data.prompt_id, directory=request_data.directory)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt '{request_data.prompt_id}' not found for expansion.")

        expanded_content, dependencies, warnings = prompt_service.expand_prompt_content(prompt.id)
        
        return PromptExpandResponse(
            prompt_id=prompt.id,
            original_content=prompt.content,
            expanded_content=expanded_content,
            dependencies=dependencies,
            warnings=warnings
        )
    except ValueError as ve:
        logger.error(f"ValueError expanding prompt: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.opt(exception=True).error(f"Error expanding prompt: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during prompt expansion")

@router.post("/rename", response_model=Dict)
async def rename_prompt_endpoint(
    rename_data: PromptRenameRequest,
    prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)
):
    """Rename an existing prompt using the new schema."""
    logger.info(f"Renaming prompt from '{rename_data.old_id}' to '{rename_data.new_name}'")

    # Sanitize the new_name
    original_new_name = rename_data.new_name
    sanitized_new_name = original_new_name.replace(" ", "_")

    if original_new_name != sanitized_new_name:
        logger.info(f"Sanitizing new_name for rename: '{original_new_name}' -> '{sanitized_new_name}'")
        rename_data.new_name = sanitized_new_name
    
    # Get the old prompt to check if it exists
    old_prompt_obj = prompt_service.get_prompt(rename_data.old_id)
    if not old_prompt_obj:
        raise HTTPException(status_code=404, detail=f"Prompt '{rename_data.old_id}' not found.")

    # Generate the new ID from directory and new name
    from src.models.unified_prompt import Prompt
    new_id = Prompt.generate_id(old_prompt_obj.directory, rename_data.new_name)
    
    # Check if a prompt with the new ID already exists
    if new_id != old_prompt_obj.id:  # Only check if the ID would actually change
        target_prompt_exists = prompt_service.get_prompt(new_id)
        if target_prompt_exists:
            detail_msg = f"Prompt with ID '{new_id}' already exists."
            if original_new_name != rename_data.new_name:
                detail_msg += f" (Original new name '{original_new_name}' was sanitized to '{rename_data.new_name}')"
            raise HTTPException(status_code=409, detail=detail_msg) # 409 Conflict

    success = prompt_service.rename_prompt(
        old_identifier=rename_data.old_id,
        new_name=rename_data.new_name,
        content=rename_data.content,
        description=rename_data.description,
        tags=rename_data.tags
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to rename prompt '{rename_data.old_id}'. Check server logs for details.")

    # If successful, return the new prompt details
    renamed_prompt = prompt_service.get_prompt(new_id)
    if not renamed_prompt:
        logger.error(f"Failed to retrieve prompt '{new_id}' after successful rename operation.")
        raise HTTPException(status_code=500, detail="Error retrieving prompt after rename.")

    prompt_dict = renamed_prompt.dict()
    prompt_dict["directory_name"] = get_directory_name(renamed_prompt.directory)
    
    # Include a message about sanitization if it occurred
    if original_new_name != renamed_prompt.name:
        prompt_dict["sanitized_message"] = f"Original new name '{original_new_name}' was sanitized to '{renamed_prompt.name}'."
    
    return prompt_dict

# --- Filesystem Path Completion Endpoint ---
from src.services.filesystem_service import FilesystemService

@router.post("/filesystem/complete_path", response_model=FilesystemCompletionResponse)
async def complete_path(request: FilesystemPathRequest):
    fs_service = FilesystemService()
    result = fs_service.get_path_completions(request.partial_path)
    return FilesystemCompletionResponse(
        completed_path=result.completed_path,
        suggestions=result.suggestions,
        is_directory=result.is_directory
    )

# ========================================
# SPECIFIC ROUTES - MUST come BEFORE catch-all routes
# ========================================

@router.post("/", response_model=Dict, status_code=201)
async def create_new_prompt(
    prompt_data: PromptCreate,
    prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)
):
    """Create a new prompt with the new ID schema."""
    original_name = prompt_data.name
    sanitized_name = original_name.replace(" ", "_")
    # Potentially add more sanitization here (e.g., for other URL-unsafe chars)
    # For now, just replacing spaces.

    if original_name != sanitized_name:
        logger.info(f"Sanitizing prompt name: '{original_name}' -> '{sanitized_name}'")
        prompt_data.name = sanitized_name

    logger.info(f"PromptAPI: create_new_prompt called for name: '{prompt_data.name}' (original: '{original_name}'), directory: '{prompt_data.directory}'")
    
    # Generate the full ID from directory and name
    from src.models.unified_prompt import Prompt
    prompt_id = Prompt.generate_id(prompt_data.directory, prompt_data.name)
    
    # Check if the prompt with this ID already exists
    if prompt_service.get_prompt(prompt_id):
        logger.warning(f"Prompt with ID already exists: {prompt_id}")
        detail_msg = f"Prompt with ID '{prompt_id}' already exists."
        if original_name != prompt_data.name:
            detail_msg += f" (Original name '{original_name}' was sanitized to '{prompt_data.name}')"
        raise HTTPException(status_code=400, detail=detail_msg)
    
    # Print the incoming data for debugging
    import json
    logger.info(f"Prompt data: {json.dumps(prompt_data.dict(), indent=2)}")
    
    # Validate directory
    if not prompt_data.directory:
        logger.error("Directory is missing")
        raise HTTPException(status_code=400, detail="Directory is required")
        
    try:
        new_prompt = prompt_service.create_prompt(
            name=prompt_data.name,
            content=prompt_data.content if prompt_data.content is not None else "",
            directory=prompt_data.directory,
            description=prompt_data.description,
            tags=prompt_data.tags if prompt_data.tags is not None else []
        )
        
        prompt_dict = new_prompt.dict()
        prompt_dict["directory_name"] = get_directory_name(new_prompt.directory)
        
        # Include sanitization message if needed
        if original_name != new_prompt.name:
            prompt_dict["sanitized_message"] = f"Original name '{original_name}' was sanitized to '{new_prompt.name}'."
        
        return prompt_dict
        
    except ValueError as ve:
        logger.error(f"ValueError creating prompt: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.opt(exception=True).error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating prompt")

@router.get("/{prompt_id:path}/referenced_by", response_model=List[Dict])
async def get_prompt_references(prompt_id: str, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Get all prompts that reference the given prompt_id."""
    logger.info(f"Fetching references for prompt_id: {prompt_id}")
    references = prompt_service.get_references_to_prompt(prompt_id)
    if references is None: # Prompt doesn't exist, return empty list instead of 404
        logger.warning(f"Prompt '{prompt_id}' not found when trying to get its references. Returning empty list.")
        return []
    return references

@router.put("/{prompt_id:path}", response_model=Dict)
async def update_existing_prompt(prompt_id: str, update_data: PromptUpdate, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Update an existing prompt's content, description, or tags."""
    logger.info(f"Updating prompt: {prompt_id} with data: {update_data.model_dump(exclude_none=True)}")
    
    prompt = prompt_service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")

    # Update fields if provided in the update_data
    updated_fields = False
    if update_data.content is not None:
        prompt.content = update_data.content
        updated_fields = True
    
    if update_data.description is not None:
        prompt.description = update_data.description
        updated_fields = True
        
    if update_data.tags is not None:
        prompt.tags = update_data.tags
        updated_fields = True

    if updated_fields:
        prompt.updated_at = datetime.now(timezone.utc) # Ensure updated_at is set
        if not prompt_service.save_prompt(prompt):
            logger.error(f"Failed to save updated prompt {prompt_id}")
            raise HTTPException(status_code=500, detail=f"Error saving prompt '{prompt_id}'")
        logger.info(f"Prompt {prompt_id} updated and saved.")
    else:
        logger.info(f"No fields to update for prompt {prompt_id}. Save not called.")

    # Retrieve the prompt again to ensure we have the latest version (especially updated_at)
    # Or trust that the in-memory `prompt` object is sufficiently updated by save_prompt if it modifies it in place.
    # For safety, re-fetch or ensure save_prompt returns the updated prompt object if it modifies it.
    # Assuming save_prompt modifies the passed `prompt` object in place including `updated_at` if applicable.
    updated_prompt_obj = prompt_service.get_prompt(prompt_id) # Re-fetch to be safe
    if not updated_prompt_obj:
        logger.error(f"Prompt {prompt_id} not found after supposedly successful update/save.")
        raise HTTPException(status_code=500, detail=f"Error retrieving prompt '{prompt_id}' after update.")

    prompt_dict = updated_prompt_obj.dict()
    prompt_dict["directory_name"] = get_directory_name(updated_prompt_obj.directory)
    return prompt_dict

@router.delete("/{prompt_id:path}", response_model=Dict)
async def delete_existing_prompt(prompt_id: str, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """Delete an existing prompt."""
    if not prompt_service.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found or could not be deleted")
    return {"message": f"Prompt '{prompt_id}' deleted successfully"}

# ========================================
# CATCH-ALL ROUTE - MUST come LAST to avoid conflicts
# ========================================

@router.get("/{prompt_id:path}", response_model=Dict)
async def get_prompt_by_id(prompt_id: str, directory: Optional[str] = None, prompt_service: PromptServiceClass = Depends(get_prompt_service_dependency)):
    """
    Get a specific prompt by ID.
    
    If multiple prompts have the same ID, you can specify a directory to disambiguate.
    """
    prompt = prompt_service.get_prompt(prompt_id, directory)
    
    # If not found and the ID contains spaces, try converting spaces to underscores
    if not prompt and ' ' in prompt_id:
        normalized_id = prompt_id.replace(' ', '_')
        prompt = prompt_service.get_prompt(normalized_id, directory)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_id}' not found")
    
    prompt_dict = prompt.dict() # Raw prompt data

    # Prepare directory_info structure
    dir_config = get_directory_by_path(prompt.directory) # This is from src.services.prompt_dirs
    if dir_config: # If directory is found in configured list
        directory_display_name = dir_config.get("name", os.path.basename(prompt.directory))
        directory_actual_path = dir_config.get("path", prompt.directory) # Should ideally be prompt.directory
    else: # Fallback for prompts whose directory might not be in current config (e.g. orphaned)
        directory_display_name = os.path.basename(prompt.directory)
        directory_actual_path = prompt.directory

    prompt_dict["directory_info"] = {
        "name": directory_display_name,
        "path": directory_actual_path
    }
    
    # Clean up old flat directory_name if present, as directory_info is now the source of truth for the editor
    if "directory_name" in prompt_dict:
        del prompt_dict["directory_name"]

    # --- Add dependencies and warnings ---
    try:
        expanded_content, dependencies, warnings = prompt_service.expand_inclusions(
            prompt.content, 
            parent_directory=prompt.directory,
            parent_id=prompt.id
        )
        # dependencies is a set of prompt IDs; convert to list of dicts for UI
        prompt_dict["dependencies"] = [
            {"id": dep_id, "is_missing": prompt_service.get_prompt(dep_id) is None}
            for dep_id in dependencies
        ]
        prompt_dict["warnings"] = warnings
    except Exception as e:
        logger.error(f"Error expanding dependencies for prompt '{prompt_id}': {e}")
        prompt_dict["dependencies"] = []
        prompt_dict["warnings"] = [f"Error expanding dependencies: {e}"]

    return prompt_dict

