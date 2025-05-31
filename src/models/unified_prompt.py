"""
Unified prompt model.

This module defines a unified model for prompts with full-path unique IDs
and intelligent display name calculation.
"""

from typing import List, Optional, Dict, Set
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
import re
import os


class Prompt(BaseModel):
    """A unified prompt model with full-path unique IDs and smart display names."""
    
    id: str  # Full file path as accessed by user - globally unique
    name: str  # Filename stem - can be duplicated across directories
    filename: str
    directory: str
    content: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    unique_id: Optional[str] = None  # Deprecated, for backward compatibility
    
    # Cache for display name calculation
    display_name_cache: Optional[str] = Field(default=None, exclude=True)
    
    @property
    def full_path(self) -> str:
        """Get the full filesystem path."""
        return str(Path(self.directory) / self.filename)
    
    @property
    def is_composite(self) -> bool:
        """Check if this prompt contains inclusions."""
        return "[[" in self.content and "]]" in self.content
    
    @classmethod
    def generate_id(cls, file_path: str) -> str:
        """Generate a unique ID from the full file path.
        
        Args:
            file_path: Complete file path as accessed by user
            
        Returns:
            Full path without .md extension as unique ID
        """
        # Convert to Path for normalization
        path = Path(file_path)
        
        # Remove .md extension if present
        if path.suffix == '.md':
            path = path.with_suffix('')
            
        # Return the full path as string
        return str(path)
    
    @classmethod
    def generate_id_from_directory_and_name(cls, directory: str, name: str) -> str:
        """Generate a unique ID from directory and name.
        
        Args:
            directory: Full directory path
            name: Prompt name (filename stem)
            
        Returns:
            Full path as unique ID
        """
        file_path = os.path.join(directory, f"{name}.md")
        return cls.generate_id(file_path)
    
    @classmethod
    def parse_id(cls, prompt_id: str) -> tuple[str, str]:
        """Parse a prompt ID to extract directory and filename.
        
        Args:
            prompt_id: The full prompt ID (full path without .md)
            
        Returns:
            Tuple of (directory, filename_stem)
        """
        path = Path(prompt_id)
        directory = str(path.parent)
        filename_stem = path.name
        
        return directory, filename_stem
    
    @property
    def display_name(self) -> str:
        """Get the smart display name for this prompt.
        
        This property returns a cached display name if available,
        or triggers calculation if needed.
        """
        if self.display_name_cache is not None:
            return self.display_name_cache
        
        # If no other prompts provided for comparison, just return name
        return self.name
    
    @classmethod
    def calculate_display_name(cls, target_prompt_id: str, all_prompt_paths: List[str]) -> str:
        """Calculate the shortest unique display name for a prompt.
        
        Args:
            target_prompt_id: The full path ID of the target prompt
            all_prompt_paths: List of all prompt full path IDs for comparison
            
        Returns:
            Shortest unique display name using colon separation
        """
        if not all_prompt_paths:
            # No other prompts to compare against
            target_path = Path(target_prompt_id)
            return target_path.name
        
        # Parse the target path
        target_path = Path(target_prompt_id)
        target_name = target_path.name
        target_parts = list(target_path.parts)
        
        # Check if filename is globally unique
        filename_conflicts = []
        for prompt_path in all_prompt_paths:
            if prompt_path == target_prompt_id:
                continue
            other_path = Path(prompt_path)
            if other_path.name == target_name:
                filename_conflicts.append(prompt_path)
        
        # If filename is unique, use it
        if not filename_conflicts:
            return target_name
        
        # Find the first unique directory element
        # Compare directory paths to find where they first differ
        
        # Collect all conflicting directory paths (excluding filename)
        conflict_dirs = []
        for conflict_path in filename_conflicts:
            conflict_parts = list(Path(conflict_path).parts)
            if len(conflict_parts) > 1:
                conflict_dirs.append(conflict_parts[:-1])  # All parts except filename
        
        target_dir_parts = target_parts[:-1]  # All parts except filename
        
        # Find the first position where target differs from all conflicts
        for pos in range(len(target_dir_parts)):
            target_segment = target_dir_parts[pos]
            
            # Check if this segment is unique across all conflicts
            is_unique = True
            for conflict_dir in conflict_dirs:
                if pos < len(conflict_dir) and conflict_dir[pos] == target_segment:
                    is_unique = False
                    break
            
            if is_unique:
                # Found the first unique segment, use it
                return f"{target_segment}:{target_name}"
        
        # If no single segment is unique, build up from the first differing segments
        # Find the minimum depth needed to distinguish from all conflicts
        for depth in range(1, len(target_dir_parts) + 1):
            target_prefix = target_dir_parts[:depth]
            
            is_unique = True
            for conflict_dir in conflict_dirs:
                if len(conflict_dir) >= depth:
                    conflict_prefix = conflict_dir[:depth]
                    if target_prefix == conflict_prefix:
                        is_unique = False
                        break
            
            if is_unique:
                unique_path = ":".join(target_prefix)
                return f"{unique_path}:{target_name}"
        
        # Fallback: use full path with colons if still not unique
        return ":".join(target_parts)
    
    @classmethod
    def calculate_all_display_names(cls, prompt_data: List[Dict[str, str]]) -> Dict[str, str]:
        """Calculate display names for all prompts efficiently.
        
        Args:
            prompt_data: List of dicts with 'id' and 'name' keys
            
        Returns:
            Dictionary mapping prompt_id -> display_name
        """
        if not prompt_data:
            return {}
        
        all_prompt_ids = [p['id'] for p in prompt_data]
        display_names = {}
        
        for prompt in prompt_data:
            prompt_id = prompt['id']
            display_name = cls.calculate_display_name(prompt_id, all_prompt_ids)
            display_names[prompt_id] = display_name
        
        return display_names
    
    def set_display_name_cache(self, display_name: str) -> None:
        """Set the cached display name for this prompt."""
        self.display_name_cache = display_name
    
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
        
        # For full path IDs, we're more flexible about format
        # Just ensure it's not empty and is a valid path-like string
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
        self.id = self.generate_id_from_directory_and_name(self.directory, self.name)
        # Update unique_id for backward compatibility
        self.unique_id = self.id
        # Clear display name cache
        self.display_name_cache = None
