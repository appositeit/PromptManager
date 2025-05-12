"""
Unified prompt model.

This module defines a unified model for prompts, replacing the separate fragment
and template models with a simpler, more consistent approach.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from pathlib import Path
from enum import Enum


class PromptType(str, Enum):
    """Types of prompts in the system."""
    STANDARD = "standard"
    COMPOSITE = "composite"
    SYSTEM = "system"
    USER = "user"
    CUSTOM = "custom"


class Prompt(BaseModel):
    """A unified prompt model."""
    
    id: str
    filename: str
    directory: str
    content: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    unique_id: Optional[str] = None
    
    @property
    def full_path(self) -> str:
        """Get the full path to the prompt file."""
        return str(Path(self.directory) / self.filename)
    
    @property
    def is_composite(self) -> bool:
        """Check if this prompt is a composite prompt."""
        # Since we removed the prompt_type field, we'll determine if it's composite
        # by checking if the content contains inclusion markers
        return "[[" in self.content and "]]" in self.content
    
    @property
    def get_unique_id(self) -> str:
        """Generate a unique ID that includes both directory and filename."""
        if self.unique_id:
            return self.unique_id
        # Create a unique ID using directory path and filename
        # Use a simplified path to avoid special characters
        dir_part = Path(self.directory).name  # Just use the directory name
        return f"{dir_part}_{self.id}"
