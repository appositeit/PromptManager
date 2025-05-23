"""
Service for managing default prompt templates.
"""

import os
from typing import Dict, List
import json

from src.services.prompt_dirs import get_directory_by_path

# Default prompt templates
DEFAULT_PROMPTS = {
    # ... Remove all entries in DEFAULT_PROMPTS where id ends with '_role' and any 'role' tags ...
}


def create_default_prompt(prompt_id: str, directory_path: str) -> Dict:
    """
    Create a default prompt in the specified directory.
    
    Args:
        prompt_id: ID of the default prompt to create
        directory_path: Path to the directory to create the prompt in
        
    Returns:
        Dict: Created prompt data
    """
    if prompt_id not in DEFAULT_PROMPTS:
        raise ValueError(f"No default prompt with ID '{prompt_id}' exists")
    
    prompt_data = DEFAULT_PROMPTS[prompt_id].copy()
    prompt_data["directory"] = directory_path
    
    # Create prompt file
    directory = get_directory_by_path(directory_path)
    if not directory:
        raise ValueError(f"Directory '{directory_path}' not found")
    
    prompt_path = os.path.join(directory_path, f"{prompt_id}.md")
    
    # Create content file
    with open(prompt_path, "w") as f:
        f.write(prompt_data["content"])
    
    # Create metadata file
    metadata_path = os.path.join(directory_path, f"{prompt_id}.json")
    metadata = {
        "id": prompt_data["id"],
        "description": prompt_data["description"],
        "is_composite": prompt_data.get("is_composite", False),
        "tags": prompt_data["tags"],
        "updated_at": None
    }
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return prompt_data


def create_all_default_prompts(directory_path: str) -> List[Dict]:
    """
    Create all default prompts in the specified directory.
    
    Args:
        directory_path: Path to the directory to create the prompts in
        
    Returns:
        List[Dict]: List of created prompt data
    """
    results = []
    
    for prompt_id in DEFAULT_PROMPTS:
        try:
            prompt_data = create_default_prompt(prompt_id, directory_path)
            results.append(prompt_data)
        except Exception as e:
            print(f"Error creating default prompt '{prompt_id}': {e}")
    
    return results


def check_default_prompts_exist(directory_path: str) -> Dict[str, bool]:
    """
    Check if default prompts exist in the specified directory.
    
    Args:
        directory_path: Path to the directory to check
        
    Returns:
        Dict[str, bool]: Dictionary mapping prompt IDs to existence status
    """
    results = {}
    
    for prompt_id in DEFAULT_PROMPTS:
        prompt_path = os.path.join(directory_path, f"{prompt_id}.md")
        metadata_path = os.path.join(directory_path, f"{prompt_id}.json")
        
        results[prompt_id] = os.path.exists(prompt_path) and os.path.exists(metadata_path)
    
    return results
