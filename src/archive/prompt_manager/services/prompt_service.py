"""
Prompt service for the prompt management system.

This module provides a service for managing prompts.
"""

import os
import glob
import re
import logging
from typing import List, Optional

from prompt_manager.models.unified_prompt import Prompt, PromptType

# Set up logger
logger = logging.getLogger(__name__)


class PromptService:
    """
    Service for managing prompts.
    """
    
    _instance = None
    
    def __new__(cls, directories=None):
        """
        Create a singleton instance of the prompt service.
        """
        if cls._instance is None:
            cls._instance = super(PromptService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, directories=None):
        """
        Initialize the prompt service.
        """
        if self.initialized:
            return
        
        self.directories = directories or []
        self.prompts = []
        self.reload()
        self.initialized = True
    
    def reload(self):
        """
        Reload all prompts from disk.
        """
        self.prompts = []
        
        # Load prompts from each directory
        for directory in self.directories:
            if os.path.exists(directory):
                for file_path in glob.glob(os.path.join(directory, "*.json")):
                    try:
                        prompt = Prompt.load(file_path)
                        self.prompts.append(prompt)
                    except Exception as e:
                        logger.error(f"Error loading prompt {file_path}: {str(e)}")
        
        # Sort prompts by ID
        self.prompts.sort(key=lambda p: p.id)
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """
        Get a prompt by ID.
        """
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                return prompt
        return None
    
    def create_prompt(
        self,
        id: str,
        content: str,
        directory: str,
        prompt_type: PromptType = PromptType.STANDARD,
        description: str = "",
        tags: List[str] = []
    ) -> Prompt:
        """
        Create a new prompt.
        """
        # Check if ID is valid
        if not re.match(r"^[a-zA-Z0-9_-]+$", id):
            raise ValueError("Invalid ID. Use only letters, numbers, underscores, and hyphens.")
        
        # Check if ID is unique
        if self.get_prompt(id):
            raise ValueError(f"Prompt with ID '{id}' already exists.")
        
        # Create prompt
        prompt = Prompt(
            id=id,
            content=content,
            description=description,
            prompt_type=prompt_type,
            tags=tags
        )
        
        # Save to file
        prompt.save(directory)
        
        # Add to list
        self.prompts.append(prompt)
        
        return prompt
    
    def update_prompt(
        self,
        id: str,
        content: str,
        description: Optional[str] = None,
        prompt_type: PromptType = None,
        tags: Optional[List[str]] = None
    ) -> Prompt:
        """
        Update a prompt by ID.
        """
        # Find the prompt
        prompt = self.get_prompt(id)
        if not prompt:
            raise ValueError(f"Prompt with ID '{id}' not found.")
        
        # Update fields
        prompt.content = content
        
        if description is not None:
            prompt.description = description
        
        if prompt_type is not None:
            prompt.prompt_type = prompt_type
        
        if tags is not None:
            prompt.tags = tags
        
        # Save changes
        prompt.save(os.path.dirname(prompt.path))
        
        return prompt
    
    def delete_prompt(self, id: str):
        """
        Delete a prompt by ID.
        """
        # Find the prompt
        prompt = self.get_prompt(id)
        if not prompt:
            raise ValueError(f"Prompt with ID '{id}' not found.")
        
        # Delete the file
        prompt.delete()
        
        # Remove from list
        self.prompts = [p for p in self.prompts if p.id != id]
    
    def render_prompt(self, id: str) -> str:
        """
        Render a prompt with all inclusions expanded.
        """
        # Find the prompt
        prompt = self.get_prompt(id)
        if not prompt:
            raise ValueError(f"Prompt with ID '{id}' not found.")
        
        # Check if it's a composite prompt
        if prompt.prompt_type != PromptType.COMPOSITE:
            return prompt.content
        
        # Render inclusions
        rendered = prompt.content
        
        # Find all inclusions
        inclusion_pattern = r"\[\[([^\]]+)\]\]"
        inclusions = re.findall(inclusion_pattern, rendered)
        
        # Process each inclusion
        for inclusion_id in inclusions:
            # Find the included prompt
            included = self.get_prompt(inclusion_id)
            
            if included:
                # Recursively render the included prompt
                included_content = included.content
                if included.prompt_type == PromptType.COMPOSITE:
                    included_content = self.render_prompt(inclusion_id)
                
                # Replace the inclusion
                rendered = rendered.replace(f"[[{inclusion_id}]]", included_content)
            else:
                # If not found, replace with a placeholder
                rendered = rendered.replace(
                    f"[[{inclusion_id}]]", 
                    f"[ERROR: Prompt '{inclusion_id}' not found]"
                )
        
        return rendered
