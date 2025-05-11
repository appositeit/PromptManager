"""
Models for the prompt management system.

This module defines the data models used by the prompt management system,
including fragments, templates, and collections.
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from pathlib import Path
from enum import Enum


class PromptType(str, Enum):
    """Types of prompts in the system."""
    PROJECT_START = "project_start"
    RESUME = "resume"
    WORKER_DISPATCH = "worker_dispatch"
    CUSTOM = "custom"


class PromptFragment(BaseModel):
    """A fragment of prompt text that can be included in templates."""
    
    id: str  # Filename without extension
    filename: str
    directory: str
    content: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    @property
    def full_path(self) -> str:
        """Get the full path to the fragment file."""
        return str(Path(self.directory) / self.filename)


class PromptTemplate(BaseModel):
    """A template for building prompts from fragments."""
    
    id: str
    name: str
    description: Optional[str] = None
    type: PromptType = PromptType.CUSTOM
    content: str  # Raw content with inclusion markers
    created_at: datetime
    updated_at: datetime
    
    # Track dependencies
    fragment_dependencies: Set[str] = Field(default_factory=set)  # Set of fragment IDs this template depends on
    

class PromptCategory(BaseModel):
    """A category of related prompts."""
    
    id: str
    name: str
    description: Optional[str] = None
    templates: List[str] = Field(default_factory=list)  # List of template IDs in this category


class PromptDirectory(BaseModel):
    """Configuration for a prompt fragment directory."""
    
    path: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
