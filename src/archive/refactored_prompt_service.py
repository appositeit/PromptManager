"""
Refactored prompt service using the base resource service.

This module provides functionality for loading, parsing, and manipulating
prompts from the filesystem.
"""

import os
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

from src.models.unified_prompt import Prompt, PromptType
from src.models.prompt import PromptDirectory
from src.services.base import BaseResourceService, ResourceDirectory


class PromptService(BaseResourceService):
    """Service for managing prompts."""
    
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompt_directories.json")
    
    def __init__(self, 
                base_directories: Optional[List[str]] = None, 
                auto_load: bool = True):
        """
        Initialize the prompt service.
        
        Args:
            base_directories: List of directories containing prompts
            auto_load: Whether to automatically load prompts on initialization
        """
        super().__init__(base_directories, self.CONFIG_FILE, False)
        self.prompts = {}  # Store prompts by ID
        
        if auto_load:
            self.load_all_prompts()
    
    def _create_directory_object(self, path: str, name: str, description: Optional[str] = None):
        """Create a prompt directory object."""
        return PromptDirectory(
            path=path,
            name=name,
            description=description,
            enabled=True
        )
    
    @property
    def resources(self) -> Dict[str, Prompt]:
        """Get all prompts."""
        return self.prompts
    
    @resources.setter
    def resources(self, value):
        """Set all prompts."""
        self.prompts = value
        
    def load_all_prompts(self) -> int:
        """
        Load all prompts from all directories.
        
        Returns:
            Number of prompts loaded
        """
        count = 0
        logger.debug(f"Loading prompts from {len(self.directories)} directories")
        
        for directory in self.directories:
            if not directory.enabled:
                logger.debug(f"Skipping disabled directory: {directory.path}")
                continue
                
            dir_count = self.load_prompts_from_directory(directory.path)
            logger.debug(f"Loaded {dir_count} prompts from {directory.path}")
            count += dir_count
            
        logger.info(f"Loaded {count} prompts total")
        return count
        
    def load_prompts_from_directory(self, directory: str) -> int:
        """
        Load all prompts from a directory.
        
        Args:
            directory: Path to the directory
            
        Returns:
            Number of prompts loaded
        """
        count = 0
        
        if not os.path.isdir(directory):
            logger.error(f"Directory not found or not a directory: {directory}")
            return 0
        
        logger.debug(f"Scanning directory for .md files: {directory}")
        
        # Track files found for better debugging
        md_files_found = []
            
        # Walk through all markdown files
        for root, _, files in os.walk(directory):
            md_files = [f for f in files if f.endswith('.md')]
            logger.debug(f"Found {len(md_files)} .md files in {root}")
            md_files_found.extend([os.path.join(root, f) for f in md_files])
            
            for filename in md_files:
                file_path = os.path.join(root, filename)
                try:
                    prompt = self.load_prompt(file_path)
                    if prompt:
                        self.prompts[prompt.id] = prompt
                        count += 1
                        logger.debug(f"Loaded prompt: {prompt.id} from {file_path}")
                    else:
                        logger.warning(f"Failed to load prompt from {file_path} (returned None)")
                except Exception as e:
                    logger.opt(exception=True).error(f"Error loading prompt {file_path}: {str(e)}")
        
        if count == 0 and md_files_found:
            logger.warning(f"Found {len(md_files_found)} .md files but loaded 0 prompts. Files: {md_files_found}")
                        
        return count
        
    def load_prompt(self, file_path: str) -> Optional[Prompt]:
        """
        Load a single prompt from a file.
        
        Args:
            file_path: Path to the prompt file
            
        Returns:
            The loaded prompt, or None if there was an error
        """
        logger.debug(f"Loading prompt from file: {file_path}")
        
        if not os.path.isfile(file_path):
            logger.error(f"File not found or not a file: {file_path}")
            return None
            
        try:
            # Get file stats
            stat = os.stat(file_path)
            created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
            updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            
            # Get relative path components
            path = Path(file_path)
            filename = path.name
            directory = str(path.parent)
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract front matter if present
            front_matter, content = self.extract_front_matter(content)
            
            # Extract metadata from front matter
            description = front_matter.get('description')
            tags = front_matter.get('tags', []) if isinstance(front_matter.get('tags'), list) else []
            
            # Determine prompt type
            prompt_type = PromptType.STANDARD
            
            if 'type' in front_matter:
                # Get type value
                type_value = front_matter['type']
                
                # Handle string type
                if isinstance(type_value, str):
                    try:
                        prompt_type = PromptType(type_value)
                    except ValueError:
                        logger.warning(f"Invalid prompt type in {file_path}: {type_value}")
                
                # Handle serialized PromptType objects
                elif hasattr(type_value, 'startswith') and '!!python' in str(type_value):
                    if 'system' in str(type_value).lower():
                        prompt_type = PromptType.SYSTEM
                    elif 'user' in str(type_value).lower():
                        prompt_type = PromptType.USER
                    elif 'composite' in str(type_value).lower():
                        prompt_type = PromptType.COMPOSITE
            
            # Determine if composite by checking for inclusion markers
            if "[[" in content and "]]" in content:
                # Contains potential inclusion markers, mark as composite
                prompt_type = PromptType.COMPOSITE
                logger.debug(f"Detected inclusion markers in {file_path}, setting type to COMPOSITE")
            
            # Create prompt
            prompt_id = Path(filename).stem  # filename without extension
            
            # Check if this prompt ID already exists
            if prompt_id in self.prompts:
                logger.warning(f"Prompt ID already exists: {prompt_id} - will be overwritten")
            
            logger.debug(f"Creating prompt object: id={prompt_id}, type={prompt_type}, directory={directory}")
            
            prompt = Prompt(
                id=prompt_id,
                filename=filename,
                directory=directory,
                content=content,
                description=description,
                prompt_type=prompt_type,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at
            )
            
            logger.debug(f"Successfully loaded prompt: {prompt_id} from {file_path}")
            return prompt
            
        except Exception as e:
            logger.opt(exception=True).error(f"Error loading prompt {file_path}: {str(e)}")
            return None
            
    def save_prompt(self, prompt: Prompt) -> bool:
        """
        Save a prompt to disk.
        
        Args:
            prompt: The prompt to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(prompt.directory, exist_ok=True)
            
            # Prepare metadata
            metadata = {}
            
            if prompt.description:
                metadata['description'] = prompt.description
                
            if prompt.tags:
                metadata['tags'] = prompt.tags
            
            if prompt.prompt_type != PromptType.STANDARD:
                # Store prompt type as a string instead of enum to avoid YAML serialization issues
                metadata['type'] = prompt.prompt_type.value
            
            # Create front matter
            front_matter = self.create_front_matter(metadata)
                
            # Write to file
            with open(prompt.full_path, 'w', encoding='utf-8') as f:
                f.write(front_matter + prompt.content)
                
            # Update timestamps
            now = datetime.now(timezone.utc)
            prompt.updated_at = now
            
            # Update in-memory copy
            self.prompts[prompt.id] = prompt
            
            logger.info(f"Saved prompt to {prompt.full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prompt {prompt.id}: {e}")
            return False
            
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """
        Get a prompt by ID.
        
        Args:
            prompt_id: The ID of the prompt to get
            
        Returns:
            The prompt, or None if not found
        """
        return self.prompts.get(prompt_id)
        
    def get_prompts_by_tag(self, tag: str, directory: Optional[str] = None) -> List[Prompt]:
        """
        Get all prompts with a specific tag.
        
        Args:
            tag: The tag to filter by
            directory: Optional directory to filter by
            
        Returns:
            List of matching prompts
        """
        if directory:
            return [p for p in self.prompts.values() 
                   if tag in p.tags and p.directory == directory]
        else:
            return [p for p in self.prompts.values() if tag in p.tags]
        
    def get_prompts_by_type(self, prompt_type: PromptType, directory: Optional[str] = None) -> List[Prompt]:
        """
        Get all prompts of a specific type.
        
        Args:
            prompt_type: The type to filter by
            directory: Optional directory to filter by
            
        Returns:
            List of matching prompts
        """
        if directory:
            return [p for p in self.prompts.values() 
                   if p.prompt_type == prompt_type and p.directory == directory]
        else:
            return [p for p in self.prompts.values() if p.prompt_type == prompt_type]
        
    def find_prompts(self, search: str) -> List[Prompt]:
        """
        Find prompts matching a search term.
        
        Args:
            search: Search term to match against ID, content, or description
            
        Returns:
            List of matching prompts
        """
        search = search.lower()
        results = []
        
        for prompt in self.prompts.values():
            if (search in prompt.id.lower() or
                (prompt.description and search in prompt.description.lower()) or
                search in prompt.content.lower()):
                results.append(prompt)
                
        return results
        
    def create_prompt(self, 
                    id: str, 
                    content: str,
                    directory: str,
                    prompt_type: PromptType = PromptType.STANDARD,
                    description: Optional[str] = None,
                    tags: List[str] = None) -> Prompt:
        """
        Create a new prompt.
        
        Args:
            id: ID for the prompt
            content: Content of the prompt
            directory: Directory to save the prompt in
            prompt_type: Type of prompt
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            The created prompt
        """
        # Create filename
        filename = f"{id}.md"
        
        # Create prompt
        now = datetime.now(timezone.utc)
        
        prompt = Prompt(
            id=id,
            filename=filename,
            directory=directory,
            content=content,
            description=description,
            prompt_type=prompt_type,
            tags=tags or [],
            created_at=now,
            updated_at=now
        )
        
        # Save to disk
        self.save_prompt(prompt)
        
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """
        Delete a prompt.
        
        Args:
            prompt_id: ID of the prompt to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            logger.warning(f"Prompt not found: {prompt_id}")
            return False
            
        try:
            # Remove from disk
            os.remove(prompt.full_path)
            
            # Remove from memory
            del self.prompts[prompt_id]
            
            logger.info(f"Deleted prompt {prompt_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting prompt {prompt_id}: {e}")
            return False
    
    def expand_inclusions(self, content: str, depth: int = 0, 
                         visited: Optional[Set[str]] = None,
                         root_id: Optional[str] = None) -> Tuple[str, Set[str], List[str]]:
        """
        Expand inclusion markers in content.
        
        Args:
            content: Content with inclusion markers
            depth: Current recursion depth
            visited: Set of already visited prompt IDs to detect cycles
            root_id: ID of the root prompt being expanded (to prevent circular references)
            
        Returns:
            Tuple of (expanded content, set of prompt IDs used, list of warnings)
        """
        # Maximum recursion depth
        if depth > 10:
            warning = "Maximum inclusion depth reached, stopping recursion"
            logger.warning(warning)
            return content, set(), [warning]
            
        # Initialize visited set if not provided
        if visited is None:
            visited = set()
            
        dependencies = set()
        warnings = []
        
        def replace_inclusion(match):
            prompt_id = match.group(1)
            
            # Remove .md extension if present
            if prompt_id.endswith('.md'):
                prompt_id = prompt_id[:-3]
            
            # Check for direct cycles
            if prompt_id in visited:
                warning = f"Circular dependency detected: '{prompt_id}' has already been included in this expansion chain"
                logger.warning(warning)
                warnings.append(warning)
                return f"[[CIRCULAR DEPENDENCY: {prompt_id}]]"
            
            # Check if this would create a circular reference to the root prompt
            if root_id and prompt_id == root_id:
                warning = f"Self-reference detected: Prompt '{prompt_id}' would create a circular reference"
                logger.warning(warning)
                warnings.append(warning)
                return f"[[SELF-REFERENCE: {prompt_id}]]"
                
            # Fetch the prompt
            prompt = self.get_prompt(prompt_id)
            if not prompt:
                warning = f"Prompt not found: '{prompt_id}'"
                logger.warning(warning)
                warnings.append(warning)
                return f"[[PROMPT NOT FOUND: {prompt_id}]]"
                
            # Track dependency
            dependencies.add(prompt_id)
            
            # Recursively expand inclusions in the prompt
            new_visited = visited.copy()
            new_visited.add(prompt_id)
            
            # Pass the root_id down for circular reference detection
            actual_root_id = root_id if root_id else prompt_id
            
            expanded_content, sub_dependencies, sub_warnings = self.expand_inclusions(
                prompt.content, depth + 1, new_visited, actual_root_id)
                
            # Add sub-dependencies and warnings
            dependencies.update(sub_dependencies)
            warnings.extend(sub_warnings)
            
            return expanded_content
            
        # Replace all inclusion markers
        expanded = self.inclusion_pattern.sub(replace_inclusion, content)
        
        return expanded, dependencies, warnings
