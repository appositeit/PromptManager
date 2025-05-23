"""
Unified prompt service.

This module provides functionality for loading, parsing, and manipulating
prompts from the filesystem.
"""

import os
import re
import yaml
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

from src.models.unified_prompt import Prompt
from src.models.prompt import PromptDirectory


class PromptService:
    """Service for managing prompts."""
    
    CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompt_directories.json")
    PROJECT_ROOT_FOR_PROMPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def __init__(self, 
                base_directories: Optional[List[str]] = None, 
                auto_load: bool = True,
                create_default_directory_if_empty: bool = True):
        """
        Initialize the prompt service.
        
        Args:
            base_directories: List of directories containing prompts. (Used for initial setup or tests)
            auto_load: Whether to automatically load prompts from configured/default directories on initialization.
            create_default_directory_if_empty: If True and no directories are loaded from config,
                                               attempts to add default directories (e.g., project's ./prompts, ~/prompts).
        """
        self.directories: List[PromptDirectory] = []
        self.prompts: Dict[str, Prompt] = {}
        
        self.inclusion_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        logger.debug(f"PromptService __init__ (id: {id(self)}) started. auto_load={auto_load}, create_default_directory_if_empty={create_default_directory_if_empty}")

        # 1. Load directories from the config file
        config_loaded_directories = self._load_directories_from_config_file()
        if config_loaded_directories:
            for dir_data in config_loaded_directories:
                self.add_directory(
                    path=dir_data['path'], 
                    name=dir_data.get('name'), 
                    description=dir_data.get('description'),
                    enabled=dir_data.get('enabled', True),
                    is_loading_from_config=True # Prevents immediate re-save of config for each dir
                )
            logger.info(f"Loaded {len(self.directories)} directories from config: {self.CONFIG_FILE}")
        else:
            logger.info(f"No directories found in config file '{self.CONFIG_FILE}' or file does not exist.")

        # 2. If no directories from config AND create_default_directory_if_empty is True, add defaults.
        if not self.directories and create_default_directory_if_empty:
            logger.info("No directories from config & create_default_directory_if_empty=True. Attempting to add default prompt directories.")
            
            # Determine PROJECT_ROOT more robustly if needed, or pass it in.
            # Assuming current file is src/services/prompt_service.py
            # So, PROJECT_ROOT_FOR_PROMPTS should be the main 'prompt_manager' dir.
            
            default_dirs_to_check = [
                {"path": str(Path(self.PROJECT_ROOT_FOR_PROMPTS) / "prompts"), "name": "Project Prompts", "desc": "Default project prompts directory"},
                {"path": str(Path.home() / "prompts"), "name": "User Prompts", "desc": "Default user prompts directory (~/prompts)"}
            ]
            
            added_any_defaults = False
            for dir_info in default_dirs_to_check:
                expanded_path = os.path.expanduser(dir_info["path"])
                if os.path.isdir(expanded_path):
                    # add_directory internally handles normalization and prevents duplicates
                    # It also handles saving the config if is_loading_from_config=False (which is default)
                    if self.add_directory(path=expanded_path, name=dir_info["name"], description=dir_info["desc"], enabled=True):
                        logger.info(f"Added default directory: '{expanded_path}' as '{dir_info['name']}'.")
                        added_any_defaults = True
                else:
                    logger.warning(f"Default directory path does not exist or is not a directory, cannot add: {expanded_path}")
            
            # if added_any_defaults:
            #    self._save_directory_config() # add_directory should handle saving if not loading from config
            #    logger.info("Default directories added and config saved.")
        
        # 3. Add any explicitly passed base_directories (mostly for testing or specific initialization)
        #    These are added *after* config and defaults to allow overriding/supplementing.
        #    is_loading_from_config=True prevents re-saving for these.
        if base_directories:
            logger.info(f"Adding explicitly passed base_directories: {base_directories}")
            for directory_path in base_directories:
                # Normalize path here before passing to add_directory
                norm_path = self._normalize_path(directory_path)
                # Check if it's already effectively there from config/defaults
                if not any(d.path == norm_path for d in self.directories):
                    self.add_directory(path=norm_path, name=os.path.basename(norm_path), is_loading_from_config=True)
                else:
                    logger.debug(f"Base directory '{norm_path}' already configured. Skipping add.")
        
        # Ensure that after all directory additions, if any happened outside of initial config load, the config is saved.
        # This is a bit tricky because add_directory saves if is_loading_from_config=False.
        # The _load_directories_from_config_file part uses is_loading_from_config=True.
        # The default directory addition uses default is_loading_from_config=False, so it saves.
        # The base_directories part uses is_loading_from_config=True.
        # This should generally be okay. A final save could be added here if absolutely necessary,
        # but might be redundant.

        # 4. If auto_load is True, load all prompts from the now-configured directories.
        if auto_load:
            logger.info(f"__init__: auto_load is True. Calling load_all_prompts() for {len(self.directories)} directories.")
            count = self.load_all_prompts()
            logger.info(f"__init__: load_all_prompts() loaded {count} prompts.")
        else:
            logger.info("__init__: auto_load is False. Skipping initial load_all_prompts().")

        logger.debug(f"PromptService __init__ finished. {len(self.directories)} dirs, {len(self.prompts)} prompts.")
            
    def _normalize_path(self, path_str: str) -> str:
        """Normalize a path string: resolve ., .., handle multiple leading slashes, and remove trailing slashes."""
        normalized = os.path.normpath(path_str)

        # If os.path.normpath preserved a double leading slash (e.g., '//foo/bar'),
        # and it's not a root like '//' (which normpath would likely turn to '/'),
        # reduce it to a single leading slash.
        # This handles the test case where normpath('//multiple...') is '//multiple...'.
        if normalized.startswith(os.sep + os.sep) and len(normalized) > len(os.sep + os.sep):
            normalized = normalized[len(os.sep):]
        
        # Remove trailing slash, but not if it's the root itself.
        if normalized.endswith(os.sep) and normalized != os.sep:
            normalized = normalized.rstrip(os.sep)
        return normalized

    def _load_directories_from_config_file(self) -> List[Dict]:
        """Loads directory configurations from the JSON file."""
        if not os.path.exists(self.CONFIG_FILE):
            logger.warning(f"Directory config file not found: {self.CONFIG_FILE}. Returning empty list.")
            return []
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded directory configurations from {self.CONFIG_FILE}")
            if not isinstance(data, list): # Ensure it's a list
                logger.error(f"Directory config file {self.CONFIG_FILE} does not contain a list. Found type: {type(data)}. Returning empty.")
                return []
            return data
        except json.JSONDecodeError:
            logger.opt(exception=True).error(f"Error decoding JSON from directory config file: {self.CONFIG_FILE}. Returning empty list.")
            return []
        except Exception:
            logger.opt(exception=True).error(f"Unexpected error loading directory config file: {self.CONFIG_FILE}. Returning empty list.")
            return []

    def _save_directory_config(self):
        """Saves the current directory configurations to the JSON file."""
        # Check if running in a test environment to prevent accidental writes
        # For Pytest, PYTEST_CURRENT_TEST environment variable is set
        if "PYTEST_CURRENT_TEST" in os.environ:
            # Allow specific test instances to override this if they manage their own config file
            if not hasattr(self, '_allow_test_config_write') or not self._allow_test_config_write:
                # Log a FATAL debug message if this happens unexpectedly during tests.
                logger.critical(f"FATAL DEBUG ALERT (LOGGER): GLOBAL CONFIG WRITE ATTEMPT DURING TEST! Target: {self.CONFIG_FILE}")
                # print(f"CRITICAL: Attempt to write global config {self.CONFIG_FILE} during test run blocked.")
                # import traceback
                # traceback.print_stack()
                return # Block saving during tests unless explicitly allowed by the test

        logger.debug(f"Saving directory configuration to: {self.CONFIG_FILE}")
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            # Serialize only the necessary attributes, not the full PromptDirectory objects if they have methods etc.
            config_data = [{
                "path": d.path, 
                "name": d.name, 
                "description": d.description, 
                "enabled": d.enabled
            } for d in self.directories]
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Successfully saved {len(self.directories)} directory configurations to {self.CONFIG_FILE}")
        except Exception:
            logger.opt(exception=True).error(f"Error saving directory configuration to {self.CONFIG_FILE}")

    def add_directory(self, path: str, name: Optional[str] = None, description: Optional[str] = None, enabled: bool = True, is_loading_from_config: bool = False) -> bool:
        """
        Adds a new prompt directory to the service.
        Ensures path normalization and avoids duplicates based on normalized path.

        Args:
            path: Filesystem path to the directory.
            name: Optional display name for the directory.
            description: Optional description.
            enabled: Whether the directory is initially enabled.
            is_loading_from_config: If True, suppresses saving the config immediately. 
                                    Useful during initial bulk load from config file.
        
        Returns:
            bool: True if the directory was newly added, False if it already existed or path was invalid.
        """
        normalized_path = self._normalize_path(path)

        if not os.path.isdir(normalized_path):
            logger.warning(f"Attempted to add directory, but path is not a valid directory: {normalized_path}")
            return False

        # Check for duplicates by normalized path
        if any(d.path == normalized_path for d in self.directories):
            logger.debug(f"Directory with path '{normalized_path}' already exists. Not adding again.")
            return False # Not newly added

        display_name = name if name else os.path.basename(normalized_path)
        
        directory = PromptDirectory(
            path=normalized_path,
            name=display_name,
            description=description or "",
            enabled=enabled,
            # last_scanned: Optional[datetime] = None # Potentially add later
        )
        self.directories.append(directory)
        logger.info(f"Added new directory: '{display_name}' (Path: {normalized_path}, Enabled: {enabled})")

        if not is_loading_from_config:
            self._save_directory_config()
            # If adding a new directory interactively, also load its prompts
            new_prompts_count = self.load_prompts_from_directory(directory)
            logger.info(f"Loaded {new_prompts_count} prompts from newly added directory '{directory.name}'.")
        
        return True # Successfully added a new directory
        
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
        """Clears existing prompts and reloads all prompts from all configured directories."""
        logger.info(f"LOAD_ALL_PROMPTS (id: {id(self)}): Called. Current cache size: {len(self.prompts)}. Clearing cache.")
        self.prompts.clear()  # Clear existing prompts from memory
        total_prompts_loaded = 0
        
        if not self.directories:
            logger.warning("No directories configured in PromptService. Cannot load any prompts.")
            return 0

        for directory in self.directories:
            if directory.enabled:
                logger.debug(f"Loading prompts from enabled directory: '{directory.name}' (Path: {directory.path})")
                count = self.load_prompts_from_directory(directory)
                total_prompts_loaded += count
            else:
                logger.debug(f"Skipping disabled directory: '{directory.name}' (Path: {directory.path})")
        
        logger.info(f"Finished loading all prompts. Total loaded: {total_prompts_loaded}")
        return total_prompts_loaded
        
    def load_prompts_from_directory(self, directory_obj: PromptDirectory) -> int:
        """
        Load all prompts from a specific PromptDirectory object.
        
        Args:
            directory_obj: The PromptDirectory object to load prompts from.
            
        Returns:
            Number of prompts loaded
        """
        count = 0
        logger.debug(f"LOAD_FROM_DIR: Scanning directory '{directory_obj.path}'. Files found by os.listdir: {os.listdir(directory_obj.path)}")
        
        directory_path = directory_obj.path # Use the .path attribute

        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found or not a directory: {directory_path}")
            return 0
        
        logger.debug(f"Scanning directory for .md files: {directory_path}")
        
        # Track files found for better debugging
        md_files_found = []
        
        # Walk through all markdown files
        for root, _, files in os.walk(directory_path):
            md_files = [f for f in files if f.endswith('.md')]
            logger.debug(f"Found {len(md_files)} .md files in {root}")
            md_files_found.extend([os.path.join(root, f) for f in md_files])
            
            for filename in md_files:
                file_path = os.path.join(root, filename)
                try:
                    prompt = self.load_prompt(file_path)
                    if prompt:
                        # Store the prompt using its new unique ID
                        self.prompts[prompt.id] = prompt
                        count += 1
                        logger.debug(f"Loaded prompt: {prompt.name} (ID: {prompt.id}) from {file_path}")
                    else:
                        logger.warning(f"Failed to load prompt from {file_path} (returned None)")
                except Exception as e:
                    logger.opt(exception=True).error(f"Error loading prompt {file_path}: {str(e)}")
        
        if count == 0 and md_files_found:
            logger.warning(f"Found {len(md_files_found)} .md files but loaded 0 prompts. Files: {md_files_found}")
                    
        return count
        
    def load_prompt(self, file_path: str) -> Optional[Prompt]:
        """
        Load a single prompt from a file with new ID schema.
        
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
            
            # NEW ID SCHEMA: Generate proper ID and name
            prompt_name = Path(filename).stem  # Display name (filename without extension)
            prompt_id = Prompt.generate_id(directory, prompt_name)  # Full unique ID
            
            # Create the prompt object with new schema
            logger.debug(f"Creating prompt object with new schema: id={prompt_id}, name={prompt_name}, directory={directory}")
            
            prompt = Prompt(
                id=prompt_id,
                name=prompt_name,
                filename=filename,
                directory=directory,
                content=content,
                description=description,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at
            )
            
            # Set unique_id for backward compatibility
            prompt.unique_id = prompt_id
            
            logger.debug(f"Successfully loaded prompt: {prompt_name} (ID: {prompt_id}) from {file_path}")
            return prompt
            
        except Exception as e:
            logger.opt(exception=True).error(f"Error loading prompt {file_path}: {str(e)}")
            return None
            
    def save_prompt(self, prompt: Prompt) -> bool:
        logger.debug(f"PromptService (id: {id(self)}): save_prompt CALLED for prompt.id='{prompt.id}', prompt.directory='{prompt.directory}', prompt.unique_id='{prompt.unique_id}'")
        logger.debug(f"Prompt object details: {prompt!r}") # Log repr of prompt
        try:
            # Ensure directory exists
            os.makedirs(prompt.directory, exist_ok=True)
            
            # Prepare content with front matter if needed
            final_content = prompt.content
            
            # Add front matter if we have metadata
            front_matter: Dict[str, Any] = {} # Explicitly typed
            
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
            
            # Update in-memory copy using the new ID
            self.prompts[prompt.id] = prompt
            
            logger.info(f"Saved prompt to {prompt.full_path} (ID: {prompt.id}, Name: {prompt.name})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prompt {prompt.id}: {e}")
            return False
            
    def get_prompt(self, identifier: str, directory: Optional[str] = None) -> Optional[Prompt]:
        """Get prompt by ID (full path) or name (with optional directory context).
        
        Args:
            identifier: Either a full ID (e.g., "general/restart") or a simple name (e.g., "restart")
            directory: Optional directory path to help disambiguate simple names
            
        Returns:
            The matching prompt, or None if not found
        """
        logger.debug(f"get_prompt CALLED for identifier: '{identifier}', directory: '{directory}'")
        logger.debug(f"Current prompt cache keys: {list(self.prompts.keys())}")
        
        # First try direct lookup by full ID
        if identifier in self.prompts:
            prompt = self.prompts[identifier]
            logger.debug(f"Found prompt directly by full ID '{identifier}'")
            
            # If directory specified, verify it matches
            if directory and prompt.directory != directory:
                logger.debug(f"Directory mismatch: prompt directory '{prompt.directory}' != requested '{directory}'")
                # Continue to search by name
            else:
                return prompt
        
        # If not found as full ID, try to find by name
        if '/' not in identifier:
            # This is a simple name, search all prompts
            matching_prompts = []
            for prompt in self.prompts.values():
                if hasattr(prompt, 'name') and prompt.name == identifier:
                    # If directory specified, only match prompts in that directory
                    if directory and prompt.directory != directory:
                        continue
                    matching_prompts.append(prompt)
                elif not hasattr(prompt, 'name') and prompt.id == identifier:
                    # Backward compatibility: handle old prompts without 'name' field
                    if directory and prompt.directory != directory:
                        continue
                    matching_prompts.append(prompt)
            
            if len(matching_prompts) == 1:
                logger.debug(f"Found 1 matching prompt by name '{identifier}'")
                return matching_prompts[0]
            elif len(matching_prompts) > 1:
                directories_found = [p.directory for p in matching_prompts]
                logger.warning(f"Multiple prompts with name '{identifier}' found in directories: {directories_found}")
                return matching_prompts[0]  # Return first match
        
        # Check for legacy unique_id format (backward compatibility)
        for prompt in self.prompts.values():
            if hasattr(prompt, 'unique_id') and prompt.unique_id == identifier:
                logger.debug(f"Found prompt by legacy unique_id '{identifier}'")
                return prompt
        
        logger.debug(f"Prompt '{identifier}' not found")
        return None
        
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
        
    def get_references_to_prompt(self, target_prompt_id: str) -> List[Dict]:
        """
        Find prompts that include a specific prompt ID in their content,
        either directly or transitively, and return them as dictionaries.

        Args:
            target_prompt_id: The ID of the prompt to search for as an inclusion.

        Returns:
            A list of dictionaries, each representing a prompt that includes the target_prompt_id.
            Returns None if the target_prompt_id itself is not found (as a check).
        """
        # Check if the target prompt itself exists. If not, it cannot be referenced.
        if not self.get_prompt(target_prompt_id):
            logger.warning(f"Target prompt '{target_prompt_id}' not found. Cannot find references to a non-existent prompt.")
            return None # Indicate target prompt not found

        logger.debug(f"Searching for prompts including '[[{target_prompt_id}]]' (transitively)")
        including_prompts_data = []
        
        normalized_target_id = target_prompt_id
        if normalized_target_id.endswith('.md'):
            normalized_target_id = normalized_target_id[:-3]
            
        for prompt in self.prompts.values():
            if prompt.id == normalized_target_id:
                continue

            if prompt.is_composite and prompt.content:
                _expanded_content, transitive_dependencies, _expansion_warnings = self.expand_inclusions(
                    prompt.content,
                    parent_directory=prompt.directory,
                    parent_id=prompt.id
                )
                
                if normalized_target_id in transitive_dependencies:
                    # Convert prompt object to dict for the API response
                    # You might want a specific Pydantic model for this response item later
                    including_prompts_data.append({
                        "id": prompt.id,
                        "description": prompt.description,
                        "directory": prompt.directory,
                        # Add other relevant fields as needed by the frontend
                    })
                        
        logger.debug(f"Found {len(including_prompts_data)} prompts transitively including '{normalized_target_id}'")
        return including_prompts_data

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
                    name: str,
                    content: str = "",
                    directory: str = "",
                    description: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> Prompt:
        """Create a new prompt with the new ID schema.
        
        Args:
            name: Display name for the prompt (will become filename)
            content: Prompt content
            directory: Directory path where prompt will be stored
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            The created prompt
        """
        logger.debug(f"PromptService: create_prompt CALLED with name='{name}', directory='{directory}'")
        
        # Validate required fields
        if not name:
            raise ValueError("Prompt name cannot be empty")
            
        if not directory:
            raise ValueError("Directory is required")
        
        # Generate unique ID from directory and name
        prompt_id = Prompt.generate_id(directory, name)
        
        # Check if prompt with this ID already exists
        if self.get_prompt(prompt_id):
            raise ValueError(f"Prompt with ID '{prompt_id}' already exists")
        
        # Set default content if empty
        if not content:
            content = f"# {name}\n\nEnter content here..."
            
        # Create filename
        filename = f"{name}.md"
        
        # Create prompt with new schema
        now = datetime.now(timezone.utc)
        
        prompt = Prompt(
            id=prompt_id,
            name=name,
            filename=filename,
            directory=directory,
            content=content,
            description=description,
            tags=tags or [],
            created_at=now,
            updated_at=now
        )
        
        # Set unique_id for backward compatibility
        prompt.unique_id = prompt_id
        
        logger.debug(f"PromptService: create_prompt generated ID='{prompt_id}' for name='{name}' in dir='{directory}'")
        
        # Save to disk
        if not self.save_prompt(prompt):
            raise Exception(f"Failed to save prompt to disk: {prompt.full_path}")
        
        return prompt
    
    def delete_prompt(self, prompt_identifier: str) -> bool:
        """
        Delete a prompt.
        
        Args:
            prompt_identifier: ID or name of the prompt to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        prompt = self.get_prompt(prompt_identifier)
        if not prompt:
            logger.warning(f"Prompt not found: {prompt_identifier}")
            return False
            
        try:
            # Remove from disk
            os.remove(prompt.full_path)
            
            # Remove from memory using the current ID
            if prompt.id in self.prompts:
                del self.prompts[prompt.id]
            
            # Also check for legacy unique_id format
            if hasattr(prompt, 'unique_id') and prompt.unique_id and prompt.unique_id in self.prompts:
                del self.prompts[prompt.unique_id]
            
            logger.info(f"Deleted prompt {prompt.name} (ID: {prompt.id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting prompt {prompt_identifier}: {e}")
            return False
    
    def rename_prompt(self, old_identifier: str, new_name: str, 
                     content: Optional[str] = None,
                     description: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> bool:
        """
        Rename a prompt and its underlying file.
        
        Args:
            old_identifier: Current prompt ID or name
            new_name: New prompt name (not full ID)
            content: Optional updated content
            description: Optional updated description
            tags: Optional updated tags
            
        Returns:
            True if renamed successfully, False otherwise
        """
        # Get the existing prompt
        prompt = self.get_prompt(old_identifier)
        if not prompt:
            logger.warning(f"Prompt not found for rename: {old_identifier}")
            return False
            
        try:
            # Generate new ID and paths
            old_path = prompt.full_path
            old_id = prompt.id
            new_id = Prompt.generate_id(prompt.directory, new_name)
            new_filename = f"{new_name}.md"
            new_path = os.path.join(prompt.directory, new_filename)
            
            # Check if the new path already exists
            if os.path.exists(new_path):
                logger.error(f"Cannot rename: file already exists at {new_path}")
                return False
            
            # Check if prompt with new ID already exists in memory
            if self.get_prompt(new_id):
                logger.error(f"Cannot rename: prompt with ID '{new_id}' already exists")
                return False
                
            # Update prompt properties
            prompt.id = new_id
            prompt.name = new_name
            prompt.filename = new_filename
            
            # Update content and metadata if provided
            if content is not None:
                prompt.content = content
                
            if description is not None:
                prompt.description = description
                
            if tags is not None:
                prompt.tags = tags
            
            # Update unique_id for backward compatibility
            prompt.unique_id = new_id
            
            # Save the prompt to the new file
            success = self.save_prompt(prompt)
            if not success:
                logger.error(f"Failed to save renamed prompt to {new_path}")
                return False
                
            # Remove the old file
            try:
                os.remove(old_path)
                logger.info(f"Deleted old prompt file at {old_path}")
            except Exception as e:
                logger.warning(f"Could not delete old prompt file at {old_path}: {e}")
                # Continue anyway - the important part is that the new file is created
            
            # Update the prompts dictionary
            if old_id in self.prompts:
                del self.prompts[old_id]
            
            # The new reference is already added by save_prompt
            
            logger.info(f"Successfully renamed prompt from {old_identifier} to {new_name} (new ID: {new_id})")
            return True
            
        except Exception as e:
            logger.opt(exception=True).error(f"Error renaming prompt {old_identifier} to {new_name}: {str(e)}")
            return False
    
    def expand_inclusions(self, content: str, 
                         parent_directory: Optional[str] = None,
                         inclusions: Optional[Set[str]] = None,
                         parent_id: Optional[str] = None) -> Tuple[str, Set[str], List[str]]:
        """
        Expand inclusion markers in content with directory context.
        
        Args:
            content: Content with inclusion markers
            parent_directory: Directory of the parent prompt for context resolution
            inclusions: Set of already included prompt IDs to detect cycles
            parent_id: ID of the parent prompt being expanded
            
        Returns:
            Tuple of (expanded content, set of prompt IDs used, list of warnings)
        """
        if inclusions is None:
            inclusions = set()
            if parent_id:
                inclusions.add(parent_id)
        
        all_mentioned_ids = set() # Stores all IDs encountered in [[...]]
        warnings = []

        def replace_inclusion(match):
            inclusion_text = match.group(1)
            
            # Clean up the inclusion text
            normalized_inclusion = inclusion_text
            if normalized_inclusion.endswith('.md'):
                normalized_inclusion = normalized_inclusion[:-3]

            # Only add non-empty IDs to dependencies
            if normalized_inclusion:
                all_mentioned_ids.add(normalized_inclusion)
            else:
                logger.warning(f"Empty inclusion marker '[[]]' found while expanding. Parent: {parent_id or 'Unknown'}")
                return f"[[EMPTY INCLUSION]]"

            if normalized_inclusion in inclusions:
                warning = f"Circular dependency detected: '{normalized_inclusion}' has already been included in this expansion chain"
                logger.warning(warning)
                warnings.append(warning)
                return f"[[CIRCULAR DEPENDENCY: {normalized_inclusion}]]"
            
            # Handle both full path and simple name inclusions
            target_prompt = None
            if '/' in normalized_inclusion:
                # Full path inclusion: [[general/restart]]
                target_prompt = self.get_prompt(normalized_inclusion)
            else:
                # Simple name inclusion: [[restart]]
                # Use parent directory as context for resolution
                target_prompt = self.get_prompt(normalized_inclusion, directory=parent_directory)
                
                # If not found in parent directory, try global search
                if not target_prompt:
                    target_prompt = self.get_prompt(normalized_inclusion)
                    
                    # If multiple matches exist, warn about ambiguity
                    matching_prompts = []
                    for prompt in self.prompts.values():
                        prompt_name = getattr(prompt, 'name', prompt.id)
                        if prompt_name == normalized_inclusion:
                            matching_prompts.append(prompt)
                    
                    if len(matching_prompts) > 1:
                        directories = [p.directory for p in matching_prompts]
                        warning = f"Ambiguous inclusion '{normalized_inclusion}' found in multiple directories: {directories}. Using first match."
                        logger.warning(warning)
                        warnings.append(warning)
                
            if not target_prompt:
                warning = f"Prompt '{normalized_inclusion}' not found"
                logger.warning(warning)
                warnings.append(warning)
                return f"[[PROMPT NOT FOUND: {normalized_inclusion}]]"
                
            new_inclusions_for_recursion = inclusions.copy()
            new_inclusions_for_recursion.add(normalized_inclusion)
            
            # Pass the target prompt's directory as context for nested inclusions
            expanded_sub_content, sub_dependencies, sub_warnings = self.expand_inclusions(
                target_prompt.content, 
                parent_directory=target_prompt.directory,
                inclusions=new_inclusions_for_recursion, 
                parent_id=target_prompt.id
            )
            
            all_mentioned_ids.update(sub_dependencies)
            warnings.extend(sub_warnings)
            
            return expanded_sub_content
            
        expanded_content_str = self.inclusion_pattern.sub(replace_inclusion, content)
        
        return expanded_content_str, all_mentioned_ids, warnings

    def expand_prompt_content(self, prompt_id: str) -> Tuple[str, List[str], List[str]]:
        """
        Expand a prompt's content by recursively including all dependencies.
        
        Args:
            prompt_id: The unique ID of the prompt to expand
            
        Returns:
            Tuple of (expanded_content, dependencies_list, warnings_list)
        """
        logger.debug(f"Expanding prompt content for: {prompt_id}")
        prompt = self.prompts.get(prompt_id)
        if not prompt:
            # Try to find by name or legacy ID
            prompt = self.get_prompt(prompt_id)
            if not prompt:
                raise ValueError(f"Prompt not found: {prompt_id}")
            
        # Use the existing expand_inclusions method with directory context
        expanded_content, dependencies_set, warnings_list = self.expand_inclusions(
            content=prompt.content,
            parent_directory=prompt.directory,
            inclusions=set(),  # Start with an empty set
            parent_id=prompt.id
        )
        
        # Convert the dependencies set to a list for the API response
        dependencies_list = list(dependencies_set)
        
        return expanded_content, dependencies_list, warnings_list
    
    def get_all_prompts(self, force_reload: bool = False, include_content: bool = False) -> List[Dict]:
        """
        Get a list of all prompts, optionally reloading from disk.
        Returns a list of dictionaries suitable for API responses (minimal data).
        """
        logger.debug(f"GET_ALL_PROMPTS (id: {id(self)}): Called. force_reload={force_reload}. Cache empty? {not self.prompts}. Cache size: {len(self.prompts)}")
        if force_reload or not self.prompts:
            logger.info("get_all_prompts: force_reload is True or no prompts in cache. Calling load_all_prompts().")
            self.load_all_prompts()
        
        prompts_list = []
        for prompt_obj in self.prompts.values():
            prompt_dict = {
                "id": prompt_obj.id,
                "name": getattr(prompt_obj, 'name', prompt_obj.id),  # Use name field if available, fallback to id
                "description": prompt_obj.description,
                "tags": prompt_obj.tags,
                "directory": prompt_obj.directory,
                "filename": prompt_obj.filename,
                "unique_id": prompt_obj.unique_id,
                "is_composite": prompt_obj.is_composite, 
                "updated_at": prompt_obj.updated_at.isoformat() if prompt_obj.updated_at else None,
                "created_at": prompt_obj.created_at.isoformat() if prompt_obj.created_at else None,
            }
            if include_content:
                prompt_dict["content"] = prompt_obj.content
            prompts_list.append(prompt_dict)
            
        return prompts_list

    def search_prompt_suggestions(self, query: str, exclude_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search for prompt suggestions based on a query string.
        Used for autocompletion in the editor, e.g., for [[prompt_name]].

        Args:
            query: The partial string to search for in prompt IDs.
            exclude_id: An optional prompt ID (simple ID) to exclude from suggestions (e.g., the current prompt being edited).

        Returns:
            A list of dictionaries, each with an 'id' key representing the prompt's simple ID.
        """
        suggestions: List[Dict[str, str]] = []
        
        # Process all prompts for empty query (when just '[[' is typed)
        # Or filter by the query string
        query_lower = query.lower() if query else ""

        for prompt in self.prompts.values():
            # Exclude the current prompt being edited if its simple ID is provided
            if exclude_id and prompt.id == exclude_id:
                continue
            
            # For empty queries, include all prompts
            # For non-empty queries, filter by the query string
            if not query or query_lower in prompt.id.lower():
                suggestions.append({"id": prompt.id}) # Frontend expects a list of dicts with 'id'
        
        # Sort suggestions alphabetically
        suggestions.sort(key=lambda x: x["id"].lower())
        
        # Limit the number of results to prevent overwhelming the UI
        max_results = 50
        if len(suggestions) > max_results:
            suggestions = suggestions[:max_results]
        
        logger.debug(f"Found {len(suggestions)} suggestions for query '{query}' (excluding '{exclude_id}')")
        return suggestions
        
    def find_prompts_by_inclusion(self, prompt_id: str) -> List[Prompt]:
        """
        Find all prompts that include (directly or indirectly) a specific prompt.
        
        Args:
            prompt_id: The ID of the prompt to search for as an inclusion.
            
        Returns:
            A list of Prompt objects that include the specified prompt.
        """
        logger.debug(f"Finding prompts that include '{prompt_id}' (directly or indirectly)")
        result = []
        
        # Normalize prompt ID to handle extensions
        normalized_target_id = prompt_id
        if normalized_target_id.endswith('.md'):
            normalized_target_id = normalized_target_id[:-3]
            
        # First check if the target prompt exists
        if not self.get_prompt(normalized_target_id):
            logger.warning(f"Target prompt '{normalized_target_id}' not found. Cannot find prompts including it.")
            return []
            
        # For each prompt, check if it includes the target
        for prompt in self.prompts.values():
            if prompt.id == normalized_target_id:
                continue  # Skip the target itself
                
            if prompt.is_composite:
                # Get all transitive dependencies through expand_inclusions
                _, transitive_dependencies, _ = self.expand_inclusions(
                    prompt.content,
                    parent_directory=prompt.directory,
                    parent_id=prompt.id
                )
                
                if normalized_target_id in transitive_dependencies:
                    result.append(prompt)
                    
        logger.debug(f"Found {len(result)} prompts including '{normalized_target_id}'")
        return result

    def get_all_prompts_including_disabled(self, include_content: bool = False) -> List[Dict]:
        """
        Get a list of all prompts, including those from disabled directories.
        Returns a list of dictionaries suitable for API responses (minimal data).
        """
        logger.debug(f"GET_ALL_PROMPTS_INCLUDING_DISABLED (id: {id(self)}): Called. Cache size: {len(self.prompts)}")
        prompts_list = []
        for directory in self.directories:
            # Load prompts from this directory regardless of enabled status
            if not os.path.isdir(directory.path):
                logger.warning(f"Directory not found or not a directory: {directory.path}")
                continue
            for root, _, files in os.walk(directory.path):
                md_files = [f for f in files if f.endswith('.md')]
                for filename in md_files:
                    file_path = os.path.join(root, filename)
                    prompt = self.load_prompt(file_path)
                    if prompt:
                        prompt_dict = {
                            "id": prompt.id,
                            "name": getattr(prompt, 'name', prompt.id),
                            "description": prompt.description,
                            "tags": prompt.tags,
                            "directory": prompt.directory,
                            "filename": prompt.filename,
                            "unique_id": prompt.unique_id,
                            "is_composite": getattr(prompt, 'is_composite', False),
                            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
                            "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
                        }
                        if include_content:
                            prompt_dict["content"] = prompt.content
                        prompts_list.append(prompt_dict)
        return prompts_list