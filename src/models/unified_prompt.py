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
    prompt_type: PromptType = PromptType.STANDARD
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    @property
    def full_path(self) -> str:
        """Get the full path to the prompt file."""
        return str(Path(self.directory) / self.filename)
    
    @property
    def is_composite(self) -> bool:
        """Check if this prompt is a composite prompt."""
        return self.prompt_type == PromptType.COMPOSITE
