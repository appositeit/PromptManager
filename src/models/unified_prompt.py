"""
Unified prompt model.

This module defines a unified model for prompts with proper ID uniqueness.
The new schema ensures that prompt IDs are globally unique while maintaining
clear separation between display names and internal identifiers.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
import re


class Prompt(BaseModel):
    """A unified prompt model with proper ID uniqueness."""
    
    id: str  # Full path: "directory_name/filename_stem" - globally unique
    name: str  # Display name: just the filename stem - can be duplicated
    filename: str
    directory: str
    content: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    unique_id: Optional[str] = None  # Deprecated, for backward compatibility
    
    @property
    def full_path(self) -> str:
        """Get the full filesystem path."""
        return str(Path(self.directory) / self.filename)
    
    @property
    def is_composite(self) -> bool:
        """Check if this prompt contains inclusions."""
        return "[[" in self.content and "]]" in self.content
    
    @classmethod
    def generate_id(cls, directory: str, name: str) -> str:
        """Generate a unique ID from directory and name.
        
        Args:
            directory: Full directory path
            name: Prompt name (filename stem)
            
        Returns:
            Unique ID in format "directory_name/name"
        """
        # Extract the last component of the directory path for the ID
        dir_path = Path(directory)
        base_name = dir_path.name or "root"  # Handle root directory edge case
        
        # Clean up any problematic characters in the directory name
        clean_dir_name = re.sub(r'[^\w\-_]', '_', base_name)
        clean_name = re.sub(r'[^\w\-_]', '_', name)
        
        return f"{clean_dir_name}/{clean_name}"
    
    @classmethod
    def parse_id(cls, prompt_id: str) -> tuple[str, str]:
        """Parse a prompt ID to extract directory name and prompt name.
        
        Args:
            prompt_id: The full prompt ID (e.g., "general/restart")
            
        Returns:
            Tuple of (directory_name, prompt_name)
        """
        if '/' in prompt_id:
            return prompt_id.split('/', 1)
        else:
            # Handle legacy IDs that might not have directory prefix
            return "", prompt_id
    
    @property
    def get_unique_id(self) -> str:
        """Backward compatibility - return the new ID."""
        return self.id
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        """Ensure ID follows the expected format."""
        if not v:
            raise ValueError("ID cannot be empty")
        
        # Allow both new format (dir/name) and legacy format (name only) during transition
        if '/' in v:
            parts = v.split('/')
            if len(parts) != 2 or not all(parts):
                raise ValueError("ID must be in format 'directory/name' with non-empty parts")
        
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure name is valid."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    def update_id_from_directory_and_name(self):
        """Update the ID based on current directory and name.
        
        This method should be called when directory or name changes
        to ensure ID remains consistent.
        """
        self.id = self.generate_id(self.directory, self.name)
        # Update unique_id for backward compatibility
        self.unique_id = self.id
