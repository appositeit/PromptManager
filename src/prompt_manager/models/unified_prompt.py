"""
Unified prompt model for the prompt management system.

This module provides a data model for prompts in the system.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import os
import json
from datetime import datetime


class PromptType(str, Enum):
    """
    Enum for prompt types.
    """
    STANDARD = "standard"
    COMPOSITE = "composite"
    SYSTEM = "system"
    USER = "user"


class Prompt(BaseModel):
    """
    Unified prompt model.
    """
    id: str
    content: str
    description: str = ""
    prompt_type: PromptType = PromptType.STANDARD
    tags: List[str] = []
    path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def save(self, directory: str):
        """
        Save the prompt to a file.
        """
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Set timestamps
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        
        # Set file path
        file_path = os.path.join(directory, f"{self.id}.json")
        self.path = file_path
        
        # Save to file
        with open(file_path, "w") as f:
            f.write(json.dumps(self.dict(), indent=2))
        
        return self
    
    @classmethod
    def load(cls, path: str) -> "Prompt":
        """
        Load a prompt from a file.
        """
        with open(path, "r") as f:
            data = json.loads(f.read())
        
        # Create prompt
        prompt = cls(**data)
        prompt.path = path
        
        return prompt
    
    def delete(self):
        """
        Delete the prompt file.
        """
        if self.path and os.path.exists(self.path):
            os.remove(self.path)
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Convert to dictionary.
        """
        data = super().dict(*args, **kwargs)
        
        # Add metadata for UI
        data["metadata"] = {
            "is_composite": self.prompt_type == PromptType.COMPOSITE,
            "has_inclusions": "[[" in self.content and "]]" in self.content,
            "word_count": len(self.content.split()),
            "char_count": len(self.content)
        }
        
        return data
