"""
Tests for the prompt_service module.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.services.prompt_service import PromptService
from src.models.prompt import PromptDirectory
from src.models.unified_prompt import Prompt


class TestPromptService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a few test prompt directories
        self.prompt_dirs = [
            os.path.join(self.test_dir, "prompts1"),
            os.path.join(self.test_dir, "prompts2"),
        ]
        
        # Create the directories
        for dir_path in self.prompt_dirs:
            os.makedirs(dir_path)
            
        # Create a test prompt service with a fresh instance
        # This ensures we're not keeping directories from previous tests
        # Use a custom config file to avoid affecting the global one
        with patch('src.services.prompt_service.PromptService.CONFIG_FILE', 
                   os.path.join(self.test_dir, "test_prompt_directories.json")):
            self.prompt_service = PromptService(base_directories=[], auto_load=False)
        
        # Sample prompts for testing
        self.sample_prompts = {
            "standard": {
                "id": "test_standard",
                "content": "This is a standard prompt.",
                "description": "A standard test prompt",
                "tags": ["test", "standard"]
            },
            "composite": {
                "id": "test_composite",
                "content": "This is a composite prompt with inclusions: [[test_standard]]",
                "description": "A composite test prompt",
                "tags": ["test", "composite"]
            }
        }
        
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_add_directory(self):
        """Test adding a directory"""
        # First make sure we start with an empty list
        self.assertEqual(len(self.prompt_service.directories), 0, 
                         "Should start with no directories")
        
        # Now add a directory
        result = self.prompt_service.add_directory(self.prompt_dirs[0])
        self.assertTrue(result)
        self.assertEqual(len(self.prompt_service.directories), 1)
        self.assertEqual(self.prompt_service.directories[0].path, self.prompt_dirs[0])
        
    def test_remove_directory(self):
        """Test removing a directory"""
        # First make sure we start with an empty list
        self.assertEqual(len(self.prompt_service.directories), 0, 
                         "Should start with no directories")
        
        # Add a directory
        self.prompt_service.add_directory(self.prompt_dirs[0])
        self.assertEqual(len(self.prompt_service.directories), 1)
        
        # Then remove it
        result = self.prompt_service.remove_directory(self.prompt_dirs[0])
        self.assertTrue(result)
        self.assertEqual(len(self.prompt_service.directories), 0)
        
    def test_create_prompt(self):
        """Test creating a new prompt"""
        # First add a directory
        self.prompt_service.add_directory(self.prompt_dirs[0])
        
        # Create a prompt
        prompt = self.prompt_service.create_prompt(
            id=self.sample_prompts["standard"]["id"],
            content=self.sample_prompts["standard"]["content"],
            directory=self.prompt_dirs[0],
            description=self.sample_prompts["standard"]["description"],
            tags=self.sample_prompts["standard"]["tags"]
        )
        
        # Check prompt properties
        self.assertEqual(prompt.id, self.sample_prompts["standard"]["id"])
        self.assertEqual(prompt.content, self.sample_prompts["standard"]["content"])
        self.assertEqual(prompt.directory, self.prompt_dirs[0])
        
        # Check if prompt file was created
        expected_file_path = os.path.join(self.prompt_dirs[0], f"{prompt.id}.md")
        self.assertTrue(os.path.exists(expected_file_path))
        
    def test_get_prompt(self):
        """Test getting a prompt by ID"""
        # First add a directory and create a prompt
        self.prompt_service.add_directory(self.prompt_dirs[0])
        prompt = self.prompt_service.create_prompt(
            id=self.sample_prompts["standard"]["id"],
            content=self.sample_prompts["standard"]["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Get the prompt
        retrieved_prompt = self.prompt_service.get_prompt(self.sample_prompts["standard"]["id"])
        
        # Check if retrieved prompt matches created prompt
        self.assertIsNotNone(retrieved_prompt)
        self.assertEqual(retrieved_prompt.id, prompt.id)
        self.assertEqual(retrieved_prompt.content, prompt.content)
        
    def test_delete_prompt(self):
        """Test deleting a prompt"""
        # First add a directory and create a prompt
        self.prompt_service.add_directory(self.prompt_dirs[0])
        prompt = self.prompt_service.create_prompt(
            id=self.sample_prompts["standard"]["id"],
            content=self.sample_prompts["standard"]["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Get file path for checking later
        file_path = prompt.full_path
        
        # Delete the prompt
        result = self.prompt_service.delete_prompt(self.sample_prompts["standard"]["id"])
        
        # Check if deletion was successful
        self.assertTrue(result)
        
        # Check if prompt was removed from memory
        self.assertIsNone(self.prompt_service.get_prompt(self.sample_prompts["standard"]["id"]))
        
        # Check if file was deleted
        self.assertFalse(os.path.exists(file_path))
        
    def test_is_composite_property(self):
        """Test the is_composite property"""
        # Create a standard prompt
        standard_prompt = Prompt(
            id="standard",
            filename="standard.md",
            directory=self.prompt_dirs[0],
            content="This is a standard prompt.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Create a composite prompt
        composite_prompt = Prompt(
            id="composite",
            filename="composite.md",
            directory=self.prompt_dirs[0],
            content="This is a composite prompt: [[standard]]",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Check is_composite property
        self.assertFalse(standard_prompt.is_composite)
        self.assertTrue(composite_prompt.is_composite)
        
    def test_expand_inclusions(self):
        """Test expansion of inclusions"""
        # First add a directory and create prompts
        self.prompt_service.add_directory(self.prompt_dirs[0])
        
        # Create a standard prompt
        standard_prompt = self.prompt_service.create_prompt(
            id=self.sample_prompts["standard"]["id"],
            content=self.sample_prompts["standard"]["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Create a composite prompt that includes the standard one
        composite_prompt = self.prompt_service.create_prompt(
            id=self.sample_prompts["composite"]["id"],
            content=self.sample_prompts["composite"]["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Expand the composite prompt
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(composite_prompt.content)
        
        # Check the expansion
        self.assertIn(standard_prompt.content, expanded)
        self.assertIn(standard_prompt.id, dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_load_prompt_from_file(self):
        """Test loading a prompt from a file"""
        # Create a test prompt file
        prompt_id = "test_prompt"
        prompt_content = "# Test Prompt\n\nThis is a test prompt."
        prompt_file_path = os.path.join(self.prompt_dirs[0], f"{prompt_id}.md")
        
        os.makedirs(self.prompt_dirs[0], exist_ok=True)
        
        with open(prompt_file_path, 'w') as f:
            f.write(prompt_content)
        
        # Load the prompt
        prompt = self.prompt_service.load_prompt(prompt_file_path)
        
        # Check if prompt was loaded correctly
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt.id, prompt_id)
        self.assertEqual(prompt.content, prompt_content)
        self.assertEqual(prompt.directory, self.prompt_dirs[0])
        
    def test_load_prompt_with_front_matter(self):
        """Test loading a prompt with front matter"""
        # Create a test prompt file with front matter
        prompt_id = "test_prompt_with_front_matter"
        prompt_description = "Test prompt with front matter"
        prompt_tags = ["test", "front_matter"]
        
        front_matter = f"""---
description: {prompt_description}
tags:
  - {prompt_tags[0]}
  - {prompt_tags[1]}
---
"""
        prompt_content = "# Test Prompt\n\nThis is a test prompt with front matter."
        prompt_file_path = os.path.join(self.prompt_dirs[0], f"{prompt_id}.md")
        
        os.makedirs(self.prompt_dirs[0], exist_ok=True)
        
        with open(prompt_file_path, 'w') as f:
            f.write(front_matter + prompt_content)
        
        # Load the prompt
        prompt = self.prompt_service.load_prompt(prompt_file_path)
        
        # Check if prompt was loaded correctly
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt.id, prompt_id)
        self.assertEqual(prompt.content, prompt_content)
        self.assertEqual(prompt.description, prompt_description)
        self.assertEqual(prompt.tags, prompt_tags)
        
    def test_save_prompt_with_front_matter(self):
        """Test saving a prompt with front matter"""
        # Create a prompt with metadata
        prompt = Prompt(
            id="test_save_front_matter",
            filename="test_save_front_matter.md",
            directory=self.prompt_dirs[0],
            content="# Test Prompt\n\nThis is a test prompt with front matter.",
            description="Test prompt description",
            tags=["test", "save"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Ensure directory exists
        os.makedirs(self.prompt_dirs[0], exist_ok=True)
        
        # Save the prompt
        self.prompt_service.save_prompt(prompt)
        
        # Check if file was created
        file_path = os.path.join(self.prompt_dirs[0], prompt.filename)
        self.assertTrue(os.path.exists(file_path))
        
        # Read the file and check for front matter
        with open(file_path, 'r') as f:
            content = f.read()
            
        self.assertIn("---", content)
        self.assertIn("description: Test prompt description", content)
        self.assertIn("- test", content)
        self.assertIn("- save", content)
        
        # Load the saved prompt and check metadata
        loaded_prompt = self.prompt_service.load_prompt(file_path)
        self.assertEqual(loaded_prompt.description, prompt.description)
        self.assertEqual(set(loaded_prompt.tags), set(prompt.tags))


if __name__ == "__main__":
    unittest.main()
