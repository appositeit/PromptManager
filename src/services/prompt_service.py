"""
Unified prompt service.

This module provides functionality for loading, parsing, and manipulating
prompts from the filesystem.
"""

import os
import re
import shutil
import yaml
import json
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
import uuid

from src.models.unified_prompt import Prompt
from src.models.prompt import PromptDirectory


class PromptService:
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
        self.directories: List[PromptDirectory] = []
        self.prompts: Dict[str, Prompt] = {}
        
        # Regular expression for inclusion markers
        self.inclusion_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        # Load saved directories from config if it exists
        saved_dirs = self._load_directory_config()
        
        # Add base directories provided in constructor
        if base_directories:
            for directory in base_directories:
                self.add_directory(directory)
                
        # Add saved directories that aren't already added
        for saved_dir in saved_dirs:
            if not any(d.path == saved_dir["path"] for d in self.directories):
                self.add_directory(
                    saved_dir["path"], 
                    saved_dir.get("name"), 
                    saved_dir.get("description")
                )
        
        if auto_load:
            self.load_all_prompts()
            
    def _load_directory_config(self) -> List[Dict]:
        """Load directory configuration from disk."""
        logger.debug(f"Loading directory configuration from {self.CONFIG_FILE}")
        
        if not os.path.exists(self.CONFIG_FILE):
            logger.debug("Directory configuration file not found, creating empty list")
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            return []
            
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                dirs = json.load(f)
                logger.info(f"Loaded {len(dirs)} directories from configuration")
                return dirs
        except Exception as e:
            logger.opt(exception=True).error(f"Error loading directory configuration: {str(e)}")
            return []
            
    def _save_directory_config(self):
        """Save directory configuration to disk."""
        logger.debug(f"Saving directory configuration to {self.CONFIG_FILE}")
        
        try:
            # Convert directories to serializable format
            dirs_data = []
            for directory in self.directories:
                dirs_data.append({
                    "path": directory.path,
                    "name": directory.name,
                    "description": directory.description,
                    "enabled": directory.enabled
                })
                
            # Write to file
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(dirs_data, f, indent=2)
                
            logger.info(f"Saved {len(dirs_data)} directories to configuration")
            return True
        except Exception as e:
            logger.opt(exception=True).error(f"Error saving directory configuration: {str(e)}")
            return False
            
    def add_directory(self, path: str, name: Optional[str] = None, 
                     description: Optional[str] = None) -> bool:
        """
        Add a directory of prompts.
        
        Args:
            path: Path to the directory
            name: Optional name for the directory
            description: Optional description of the directory
            
        Returns:
            True if the directory was added, False otherwise
        """
        logger.debug(f"Adding directory: path={path}, name={name}")
        
        # Check if directory exists
        if not os.path.isdir(path):
            logger.error(f"Directory not found or not a directory: {path}")
            return False
        
        # Check if directory already exists in our list
        for existing_dir in self.directories:
            if existing_dir.path == path:
                logger.warning(f"Directory already exists in service: {path}")
                # Even though it exists, try to reload prompts from it
                count = self.load_prompts_from_directory(path)
                logger.info(f"Reloaded {count} prompts from existing directory: {path}")
                return True
            
        # If name not provided, use the directory name
        if not name:
            name = os.path.basename(path)
            
        # Add to directories list
        directory = PromptDirectory(
            path=path,
            name=name,
            description=description,
            enabled=True
        )
        
        self.directories.append(directory)
        logger.info(f"Added prompt directory: {path} (name: {name})")
        
        # Save the updated directory configuration
        self._save_directory_config()
        
        return True
        
    def remove_directory(self, path: str) -> bool:
        """
        Remove a directory from the prompt service.
        
        Args:
            path: Path to the directory to remove
            
        Returns:
            True if the directory was removed, False otherwise
        """
        logger.debug(f"Removing directory: {path}")
        
        initial_prompt_count = len(self.prompts)
        initial_directory_count = len(self.directories)
        
        # Find directory index
        directory_idx = None
        for i, directory in enumerate(self.directories):
            if directory.path == path:
                directory_idx = i
                break
                
        # Return false if directory not found
        if directory_idx is None:
            logger.warning(f"Directory not found in service: {path}")
            return False
            
        try:
            # Get list of prompts to remove
            prompts_to_remove = [p_id for p_id, p in self.prompts.items() if p.directory == path]
            logger.debug(f"Found {len(prompts_to_remove)} prompts to remove from {path}")
            
            # Remove all prompts from this directory
            for prompt_id in prompts_to_remove:
                del self.prompts[prompt_id]
                
            # Remove directory from list
            del self.directories[directory_idx]
            
            # Save the updated directory configuration
            self._save_directory_config()
            
            logger.info(f"Removed prompt directory: {path} (removed {initial_prompt_count - len(self.prompts)} prompts)")
            return True
        except Exception as e:
            logger.opt(exception=True).error(f"Error removing directory {path}: {str(e)}")
            return False
        
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
                
            # Log the content of the file for debugging (truncated for large files)
            content_preview = content[:500] + "..." if len(content) > 500 else content
            logger.debug(f"Read content from {file_path} ({len(content)} bytes): {content_preview}")
                
            # Extract front matter if present
            description = None
            tags = []
            
            if content.startswith('---'):
                # Parse YAML front matter
                end_idx = content.find('---', 3)
                if end_idx > 0:
                    front_matter = content[3:end_idx].strip()
                    logger.debug(f"Found front matter in {file_path}: {front_matter}")
                    
                    try:
                        # First try to use safe_load with special handling
                        # to prevent yaml constructor errors
                        # Replace any coordinator references with prompt_manager
                        front_matter = front_matter.replace(
                            '!!python/object/apply:coordinator.',
                            '!python_object '
                        )
                        
                        # Create a custom YAML loader
                        class CustomLoader(yaml.SafeLoader):
                            pass
                            
                        # Add a constructor for handling the old coordinator types
                        def python_object_constructor(loader, node):
                            # Just return the value as a string, we'll parse it later
                            return str(node.value)
                            
                        # Register the constructor
                        CustomLoader.add_constructor('!python_object', python_object_constructor)
                        
                        # Try to load with our custom loader
                        try:
                            meta = yaml.load(front_matter, Loader=CustomLoader)
                        except Exception as yaml_err:
                            # If that fails, try safe_load as fallback
                            logger.warning(f"Custom YAML parsing failed: {str(yaml_err)}, trying safe_load")
                            meta = yaml.safe_load(front_matter)
                        if isinstance(meta, dict):
                            description = meta.get('description')
                            if 'tags' in meta and isinstance(meta['tags'], list):
                                tags = meta['tags']

                        
                        # Remove front matter from content
                        content = content[end_idx+3:].strip()
                        logger.debug(f"Parsed front matter: description={description}, tags={tags}")
                    except Exception as e:
                        logger.opt(exception=True).warning(f"Error parsing front matter in {file_path}: {str(e)}")
                        # Continue with empty metadata but still process the file
                        meta = {}
                        # We've removed the prompt type handling
            
            # No longer need to determine composite type - it's handled by is_composite property
            
            # Create prompt
            prompt_id = Path(filename).stem  # filename without extension
            
            # Check if this prompt ID already exists
            if prompt_id in self.prompts:
                logger.warning(f"Prompt ID already exists: {prompt_id} - will be overwritten")
            
            logger.debug(f"Creating prompt object: id={prompt_id}, directory={directory}")
            
            prompt = Prompt(
                id=prompt_id,
                filename=filename,
                directory=directory,
                content=content,
                description=description,
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
            
            # Prepare content with front matter if needed
            final_content = prompt.content
            
            # Add front matter if we have metadata
            front_matter = {}
            
            if prompt.description:
                front_matter['description'] = prompt.description
                
            if prompt.tags:
                front_matter['tags'] = prompt.tags
            
            # We no longer need to store prompt_type
            
            if front_matter:
                yaml_str = yaml.dump(front_matter, default_flow_style=False)
                final_content = f"---\n{yaml_str}---\n\n{prompt.content}"
                
            # Write to file
            with open(prompt.full_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
                
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
        
    def get_composite_prompts(self, directory: Optional[str] = None) -> List[Prompt]:
        """
        Get all composite prompts (containing inclusions).
        
        Args:
            directory: Optional directory to filter by
            
        Returns:
            List of matching prompts
        """
        if directory:
            return [p for p in self.prompts.values() 
                   if p.is_composite and p.directory == directory]
        else:
            return [p for p in self.prompts.values() if p.is_composite]
        
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
                    content: str = "",
                    directory: str = "",
                    description: Optional[str] = None,
                    tags: List[str] = None) -> Prompt:
        """
        Create a new prompt.
        
        Args:
            id: ID for the prompt
            content: Content of the prompt
            directory: Directory to save the prompt in
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            The created prompt
        """
        # Validate required fields
        if not id:
            raise ValueError("Prompt ID cannot be empty")
            
        if not directory:
            raise ValueError("Directory is required")
            
        # Set default content if empty
        if not content:
            content = f"# {id}\n\nEnter content here..."
            
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
            tags=tags or [],
            created_at=now,
            updated_at=now
        )
        
        # Save to disk
        if not self.save_prompt(prompt):
            raise Exception(f"Failed to save prompt to disk: {prompt.full_path}")
        
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