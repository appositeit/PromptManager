"""
Base service for resource management.

This module provides a base class for services that manage resources
(prompts, fragments, templates) from the filesystem.
"""

import os
import re
import json
import yaml
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from loguru import logger


class ResourceDirectory:
    """Base class for resource directories."""
    
    def __init__(self, 
                path: str,
                name: str,
                description: Optional[str] = None,
                enabled: bool = True):
        """
        Initialize a resource directory.
        
        Args:
            path: Path to the directory
            name: Display name for the directory
            description: Optional description
            enabled: Whether the directory is enabled
        """
        self.path = path
        self.name = name
        self.description = description
        self.enabled = enabled


class Resource:
    """Base class for resources."""
    
    def __init__(self,
                id: str,
                filename: str,
                directory: str,
                content: str,
                description: Optional[str] = None,
                tags: Optional[List[str]] = None,
                created_at: Optional[datetime] = None,
                updated_at: Optional[datetime] = None):
        """
        Initialize a resource.
        
        Args:
            id: Resource ID
            filename: Filename
            directory: Directory path
            content: Resource content
            description: Optional description
            tags: Optional tags
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.filename = filename
        self.directory = directory
        self.content = content
        self.description = description
        self.tags = tags or []
        
        # Set timestamps
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
    
    @property
    def full_path(self) -> str:
        """Get the full path to the resource file."""
        return os.path.join(self.directory, self.filename)


class BaseResourceService:
    """Base service for managing resources from the filesystem."""
    
    def __init__(self, 
                base_directories: Optional[List[str]] = None,
                config_file: Optional[str] = None,
                auto_load: bool = True):
        """
        Initialize the base resource service.
        
        Args:
            base_directories: List of directories containing resources
            config_file: Path to configuration file for saved directories
            auto_load: Whether to automatically load resources on initialization
        """
        self.directories: List[ResourceDirectory] = []
        self.resources: Dict[str, Resource] = {}
        self.config_file = config_file
        
        # Regular expression for inclusion markers
        self.inclusion_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        # Load saved directories from config if it exists
        if config_file:
            saved_dirs = self._load_directory_config()
            
            # Add saved directories
            for saved_dir in saved_dirs:
                if not any(d.path == saved_dir["path"] for d in self.directories):
                    self.add_directory(
                        saved_dir["path"], 
                        saved_dir.get("name"), 
                        saved_dir.get("description")
                    )
        
        # Add base directories provided in constructor
        if base_directories:
            for directory in base_directories:
                self.add_directory(directory)
    
    def _load_directory_config(self) -> List[Dict]:
        """Load directory configuration from disk."""
        if not self.config_file:
            logger.debug("No config file specified for loading, returning empty list")
            return []

        logger.debug(f"Loading directory configuration from {self.config_file}")
        
        if not os.path.exists(self.config_file):
            logger.debug("Directory configuration file not found, creating empty list")
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            return []
            
        try:
            with open(self.config_file, 'r') as f:
                dirs = json.load(f)
                logger.info(f"Loaded {len(dirs)} directories from configuration")
                return dirs
        except Exception as e:
            logger.opt(exception=True).error(f"Error loading directory configuration: {str(e)}")
            return []
    
    def _save_directory_config(self):
        """Save directory configuration to disk."""
        if not self.config_file:
            logger.debug("No config file specified, skipping save")
            return False
            
        logger.debug(f"Saving directory configuration to {self.config_file}")
        
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
            with open(self.config_file, 'w') as f:
                json.dump(dirs_data, f, indent=2)
                
            logger.info(f"Saved {len(dirs_data)} directories to configuration")
            return True
        except Exception as e:
            logger.opt(exception=True).error(f"Error saving directory configuration: {str(e)}")
            return False
    
    def add_directory(self, path: str, name: Optional[str] = None, 
                     description: Optional[str] = None) -> bool:
        """
        Add a directory of resources.
        
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
                return True
            
        # If name not provided, use the directory name
        if not name:
            name = os.path.basename(path)
            
        # Create directory object - This method should be implemented by subclasses
        directory = self._create_directory_object(path, name, description)
        
        self.directories.append(directory)
        logger.info(f"Added resource directory: {path} (name: {name})")
        
        # Save the updated directory configuration
        self._save_directory_config()
        
        return True
    
    def _create_directory_object(self, path: str, name: str, description: Optional[str] = None):
        """Create a directory object - to be overridden by subclasses."""
        return ResourceDirectory(
            path=path,
            name=name,
            description=description,
            enabled=True
        )
    
    def remove_directory(self, path: str) -> bool:
        """
        Remove a directory from the service.
        
        Args:
            path: Path to the directory to remove
            
        Returns:
            True if the directory was removed, False otherwise
        """
        logger.debug(f"Removing directory: {path}")
        
        initial_resource_count = len(self.resources)
        # initial_directory_count = len(self.directories) # Unused variable
        
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
            # Get list of resources to remove
            resources_to_remove = [r_id for r_id, r in self.resources.items() if r.directory == path]
            logger.debug(f"Found {len(resources_to_remove)} resources to remove from {path}")
            
            # Remove all resources from this directory
            for resource_id in resources_to_remove:
                del self.resources[resource_id]
                
            # Remove directory from list
            del self.directories[directory_idx]
            
            # Save the updated directory configuration
            self._save_directory_config()
            
            logger.info(f"Removed resource directory: {path} (removed {initial_resource_count - len(self.resources)} resources)")
            return True
        except Exception as e:
            logger.opt(exception=True).error(f"Error removing directory {path}: {str(e)}")
            return False
    
    def extract_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract YAML front matter from content.
        
        Args:
            content: Content string potentially containing front matter
            
        Returns:
            Tuple of (front matter dict, content without front matter)
        """
        front_matter: Dict[str, Any] = {}
        
        if not content.startswith('---'):
            return front_matter, content
            
        # Parse YAML front matter
        end_idx = content.find('---', 3)
        if end_idx <= 0:
            return front_matter, content
            
        try:
            yaml_content = content[3:end_idx].strip()
            meta = yaml.safe_load(yaml_content)
            
            if isinstance(meta, dict):
                front_matter = meta
                
            # Remove front matter from content
            content = content[end_idx+3:].strip()
            
        except Exception as e:
            logger.warning(f"Error parsing front matter: {e}")
            
        return front_matter, content

    def create_front_matter(self, metadata: Dict[str, Any]) -> str:
        """
        Create YAML front matter string from metadata.
        
        Args:
            metadata: Dictionary of metadata
            
        Returns:
            YAML front matter string
        """
        if not metadata:
            return ""
            
        try:
            yaml_str = yaml.dump(metadata, default_flow_style=False)
            return f"---\n{yaml_str}---\n\n"
        except Exception as e:
            logger.warning(f"Error creating front matter: {e}")
            return ""
