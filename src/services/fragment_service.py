"""
Service for managing prompt fragments.

This module provides functionality for loading, parsing, and manipulating
prompt fragments from the filesystem.
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone
from pathlib import Path
import yaml
from loguru import logger

from src.models.prompt import PromptFragment, PromptDirectory


class FragmentService:
    """Service for managing prompt fragments."""
    
    def __init__(self, 
                base_directories: Optional[List[str]] = None, 
                auto_load: bool = True):
        """
        Initialize the fragment service.
        
        Args:
            base_directories: List of directories containing prompt fragments
            auto_load: Whether to automatically load fragments on initialization
        """
        self.directories: List[PromptDirectory] = []
        
        if base_directories:
            for directory in base_directories:
                self.add_directory(directory)
                
        self.fragments: Dict[str, PromptFragment] = {}
        
        # Regular expression for inclusion markers
        self.inclusion_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        if auto_load:
            self.load_all_fragments()
            
    def add_directory(self, path: str, name: Optional[str] = None, 
                     description: Optional[str] = None) -> bool:
        """
        Add a directory of prompt fragments.
        
        Args:
            path: Path to the directory
            name: Optional name for the directory
            description: Optional description of the directory
            
        Returns:
            True if the directory was added, False otherwise
        """
        # Check if directory exists
        if not os.path.isdir(path):
            logger.error(f"Directory not found: {path}")
            return False
            
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
        logger.info(f"Added prompt directory: {path}")
        
        return True
        
    def load_all_fragments(self) -> int:
        """
        Load all fragments from all directories.
        
        Returns:
            Number of fragments loaded
        """
        count = 0
        
        for directory in self.directories:
            if not directory.enabled:
                continue
                
            count += self.load_fragments_from_directory(directory.path)
            
        logger.info(f"Loaded {count} prompt fragments")
        return count
        
    def load_fragments_from_directory(self, directory: str) -> int:
        """
        Load all fragments from a directory.
        
        Args:
            directory: Path to the directory
            
        Returns:
            Number of fragments loaded
        """
        count = 0
        
        if not os.path.isdir(directory):
            logger.error(f"Directory not found: {directory}")
            return 0
            
        # Walk through all markdown files
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.md'):
                    try:
                        fragment = self.load_fragment(os.path.join(root, filename))
                        if fragment:
                            self.fragments[fragment.id] = fragment
                            count += 1
                    except Exception as e:
                        logger.error(f"Error loading fragment {filename}: {e}")
                        
        return count
        
    def load_fragment(self, file_path: str) -> Optional[PromptFragment]:
        """
        Load a single fragment from a file.
        
        Args:
            file_path: Path to the fragment file
            
        Returns:
            The loaded fragment, or None if there was an error
        """
        if not os.path.isfile(file_path):
            logger.error(f"File not found: {file_path}")
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
            description = None
            tags = []
            
            if content.startswith('---'):
                # Parse YAML front matter
                end_idx = content.find('---', 3)
                if end_idx > 0:
                    front_matter = content[3:end_idx].strip()
                    try:
                        meta = yaml.safe_load(front_matter)
                        if isinstance(meta, dict):
                            description = meta.get('description')
                            if 'tags' in meta and isinstance(meta['tags'], list):
                                tags = meta['tags']
                        
                        # Remove front matter from content
                        content = content[end_idx+3:].strip()
                    except Exception as e:
                        logger.warning(f"Error parsing front matter in {file_path}: {e}")
            
            # Create fragment
            fragment_id = Path(filename).stem  # filename without extension
            
            fragment = PromptFragment(
                id=fragment_id,
                filename=filename,
                directory=directory,
                content=content,
                description=description,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at
            )
            
            return fragment
            
        except Exception as e:
            logger.error(f"Error loading fragment {file_path}: {e}")
            return None
            
    def save_fragment(self, fragment: PromptFragment) -> bool:
        """
        Save a fragment to disk.
        
        Args:
            fragment: The fragment to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(fragment.directory, exist_ok=True)
            
            # Prepare content with front matter if needed
            final_content = fragment.content
            
            # Add front matter if we have description or tags
            if fragment.description or fragment.tags:
                front_matter = {}
                
                if fragment.description:
                    front_matter['description'] = fragment.description
                    
                if fragment.tags:
                    front_matter['tags'] = fragment.tags
                    
                yaml_str = yaml.dump(front_matter, default_flow_style=False)
                final_content = f"---\n{yaml_str}---\n\n{fragment.content}"
                
            # Write to file
            with open(fragment.full_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
                
            # Update timestamps
            now = datetime.now(timezone.utc)
            fragment.updated_at = now
            
            # Update in-memory copy
            self.fragments[fragment.id] = fragment
            
            logger.info(f"Saved fragment to {fragment.full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving fragment {fragment.id}: {e}")
            return False
            
    def get_fragment(self, fragment_id: str) -> Optional[PromptFragment]:
        """
        Get a fragment by ID.
        
        Args:
            fragment_id: The ID of the fragment to get
            
        Returns:
            The fragment, or None if not found
        """
        return self.fragments.get(fragment_id)
        
    def get_fragments_by_tag(self, tag: str) -> List[PromptFragment]:
        """
        Get all fragments with a specific tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of matching fragments
        """
        return [f for f in self.fragments.values() if tag in f.tags]
        
    def find_fragments(self, search: str) -> List[PromptFragment]:
        """
        Find fragments matching a search term.
        
        Args:
            search: Search term to match against ID, content, or description
            
        Returns:
            List of matching fragments
        """
        search = search.lower()
        results = []
        
        for fragment in self.fragments.values():
            if (search in fragment.id.lower() or
                (fragment.description and search in fragment.description.lower()) or
                search in fragment.content.lower()):
                results.append(fragment)
                
        return results
        
    def expand_inclusions(self, content: str, depth: int = 0, 
                         visited: Optional[Set[str]] = None) -> Tuple[str, Set[str]]:
        """
        Expand inclusion markers in content.
        
        Args:
            content: Content with inclusion markers
            depth: Current recursion depth
            visited: Set of already visited fragment IDs to detect cycles
            
        Returns:
            Tuple of (expanded content, set of fragment IDs used)
        """
        if depth > 10:
            logger.warning("Maximum inclusion depth reached, stopping recursion")
            return content, set()
            
        if visited is None:
            visited = set()
            
        dependencies = set()
        
        def replace_inclusion(match):
            fragment_id = match.group(1)
            
            # Remove .md extension if present
            if fragment_id.endswith('.md'):
                fragment_id = fragment_id[:-3]
            
            # Check for cycles
            if fragment_id in visited:
                logger.warning(f"Cyclic inclusion detected: {fragment_id}")
                return f"[[CYCLIC INCLUSION: {fragment_id}]]"
                
            fragment = self.get_fragment(fragment_id)
            if not fragment:
                logger.warning(f"Fragment not found: {fragment_id}")
                return f"[[FRAGMENT NOT FOUND: {fragment_id}]]"
                
            # Track dependency
            dependencies.add(fragment_id)
            
            # Recursively expand inclusions in the fragment
            new_visited = visited.copy()
            new_visited.add(fragment_id)
            expanded_content, sub_dependencies = self.expand_inclusions(
                fragment.content, depth + 1, new_visited)
                
            # Add sub-dependencies
            dependencies.update(sub_dependencies)
            
            return expanded_content
            
        # Replace all inclusion markers
        expanded = self.inclusion_pattern.sub(replace_inclusion, content)
        
        return expanded, dependencies
