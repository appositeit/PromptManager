"""
Prompt directory management.

This module provides functionality for initializing and managing prompt directories.
"""

import os
from typing import Dict, Optional
from loguru import logger

# Default prompt directories
def initialize_prompt_directories():
    """
    Initialize the prompt directories.
    
    This function ensures that the standard prompt directories exist.
    """
    # Project data directory
    project_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..", 
        "data", 
        "prompts"
    ))
    
    # Project prompts directory in repository root
    project_prompts_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..", 
        "prompts"
    ))
    
    # User config directory
    user_dir = os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompts")
    
    # Create directories if they don't exist
    for directory in [project_dir, project_prompts_dir, user_dir]:
        if not os.path.exists(directory):
            logger.info(f"Creating prompt directory: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    logger.info("Prompt directories initialized")
    return [project_dir, project_prompts_dir, user_dir]

def get_prompt_directories():
    """
    Get the list of prompt directories.
    
    Returns:
        List of prompt directory paths
    """
    # Project data directory
    project_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..", 
        "data", 
        "prompts"
    ))
    
    # Project prompts directory in repository root
    project_prompts_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..", 
        "prompts"
    ))
    
    # User config directory
    user_dir = os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompts")
    
    return [d for d in [project_dir, project_prompts_dir, user_dir] if os.path.exists(d)]

def get_directory_by_path(path: str) -> Optional[Dict]:
    """
    Get directory information by path.
    
    Args:
        path: Directory path
        
    Returns:
        Directory information or None if not found
    """
    # Project data directory
    project_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..", 
        "data", 
        "prompts"
    ))
    
    # Project prompts directory in repository root
    project_prompts_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        "..", 
        "..", 
        "prompts"
    ))
    
    # User config directory
    user_dir = os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompts")
    
    # Define directory info
    directories = [
        {
            "path": project_dir,
            "name": "Project Data Prompts",
            "description": "Prompts stored in the project data directory",
            "type": "project"
        },
        {
            "path": project_prompts_dir,
            "name": "Repository Prompts",
            "description": "Prompts stored in the repository root directory",
            "type": "repository"
        },
        {
            "path": user_dir,
            "name": "User Prompts",
            "description": "Prompts stored in the user's config directory",
            "type": "user"
        }
    ]
    
    # Find the directory
    for directory in directories:
        if os.path.normpath(directory["path"]) == os.path.normpath(path):
            return directory
    
    return None

def get_default_directory():
    """
    Get the default directory for creating new prompts.
    
    Returns:
        Path to the default directory
    """
    # User config directory is preferred for new prompts
    user_dir = os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompts")
    
    # Create if it doesn't exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir, exist_ok=True)
    
    return user_dir
