"""
Unit tests for the PromptService.

These tests cover the core functionality of the PromptService, including
managing prompt directories, creating, retrieving, updating, and deleting
prompts, handling composite prompts (inclusion/expansion), and
loading/saving prompts to the filesystem with and without metadata
(frontmatter).

Modules/Classes Tested:
- src.services.prompt_service.PromptService
- src.models.prompt.PromptDirectory (implicitly via directory management)
- src.models.unified_prompt.Prompt (as objects created and managed by the service)
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
import pytest

from src.services.prompt_service import PromptService
from src.models.unified_prompt import Prompt


class TestPromptService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.test_dir, "test_prompt_directories.json")
        
        # Create a few test prompt directories
        self.prompt_dirs = [
            os.path.join(self.test_dir, "prompts1"),
            os.path.join(self.test_dir, "prompts2"),
        ]
        
        # Create the directories
        for dir_path in self.prompt_dirs:
            os.makedirs(dir_path)
            
        # Store original class CONFIG_FILE and patch it for initialization
        self._original_prompt_service_config_file = PromptService.CONFIG_FILE
        PromptService.CONFIG_FILE = self.test_config_path
        
        # Create a test prompt service with a fresh instance
        self.prompt_service = PromptService(
            base_directories=[], 
            auto_load=False, 
            create_default_directory_if_empty=False
        )
        
        # IMPORTANT: Set an instance-specific CONFIG_FILE to ensure this instance
        # always uses the test config, even after class attribute is restored.
        self.prompt_service.CONFIG_FILE = self.test_config_path
        
        # Restore class attribute immediately if no other instance in this test class needs it patched during __init__
        # However, to be safe for other potential setups or if other services were created using the patch,
        # it's better to restore in tearDown. For now, the instance is protected.
        # PromptService.CONFIG_FILE = self._original_prompt_service_config_file # Not here, in tearDown

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
        # Restore the original class CONFIG_FILE
        PromptService.CONFIG_FILE = self._original_prompt_service_config_file
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
        prompt_data = self.sample_prompts["standard"]
        self.prompt_service.create_prompt(
            id=prompt_data["id"],
            content=prompt_data["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Get the prompt
        retrieved_prompt = self.prompt_service.get_prompt(prompt_data["id"])
        
        # Check if retrieved prompt matches created prompt
        self.assertIsNotNone(retrieved_prompt)
        self.assertEqual(retrieved_prompt.id, prompt_data["id"])
        self.assertEqual(retrieved_prompt.content, prompt_data["content"])
        
    def test_delete_prompt(self):
        """Test deleting a prompt"""
        # First add a directory and create a prompt
        self.prompt_service.add_directory(self.prompt_dirs[0])
        prompt_data = self.sample_prompts["standard"]
        prompt = self.prompt_service.create_prompt(
            id=prompt_data["id"],
            content=prompt_data["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Get file path for checking later
        file_path = prompt.full_path
        
        # Delete the prompt
        result = self.prompt_service.delete_prompt(prompt_data["id"])
        
        # Check if deletion was successful
        self.assertTrue(result)
        
        # Check if prompt was removed from memory
        self.assertIsNone(self.prompt_service.get_prompt(prompt_data["id"]))
        
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
        standard_prompt_data = self.sample_prompts["standard"]
        standard_prompt = self.prompt_service.create_prompt(
            id=standard_prompt_data["id"],
            content=standard_prompt_data["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Create a composite prompt that includes the standard one
        composite_prompt_data = self.sample_prompts["composite"]
        composite_prompt = self.prompt_service.create_prompt(
            id=composite_prompt_data["id"],
            content=composite_prompt_data["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Expand the composite prompt
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(composite_prompt.content)
        
        # Check the expansion
        self.assertIn(standard_prompt.content, expanded)
        self.assertIn(standard_prompt.id, dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_expand_prompt_content(self):
        """Test the expand_prompt_content method which is used by the API endpoint"""
        # First add a directory and create prompts
        self.prompt_service.add_directory(self.prompt_dirs[0])
        
        # Create a standard prompt
        standard_prompt_data = self.sample_prompts["standard"]
        standard_prompt = self.prompt_service.create_prompt(
            id=standard_prompt_data["id"],
            content=standard_prompt_data["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Create a composite prompt that includes the standard one
        composite_prompt_data = self.sample_prompts["composite"]
        composite_prompt = self.prompt_service.create_prompt(
            id=composite_prompt_data["id"],
            content=composite_prompt_data["content"],
            directory=self.prompt_dirs[0]
        )
        
        # Use expand_prompt_content with the unique_id to match API usage
        expanded, dependencies_list, warnings_list = self.prompt_service.expand_prompt_content(composite_prompt.unique_id)
        
        # Check the expansion
        self.assertIn(standard_prompt.content, expanded)
        self.assertIn(standard_prompt.id, dependencies_list)
        self.assertEqual(len(warnings_list), 0)
        self.assertIsInstance(dependencies_list, list, "Dependencies should be a list for API compatibility")
        
    def test_load_prompt_from_file(self):
        """Test loading a prompt from a file"""
        # Create a test prompt file
        prompt_id = "test_prompt_file"
        prompt_content = "# Test Prompt File\n\nThis is content from a file."
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
        prompt_id = "test_prompt_fm"
        prompt_description = "Test prompt with front matter"
        prompt_tags = ["test", "front_matter"]
        
        front_matter = f"""---
description: {prompt_description}
tags:
  - {prompt_tags[0]}
  - {prompt_tags[1]}
---
"""
        prompt_body_content = "# Test Prompt Body\n\nThis is the main content."
        prompt_file_path = os.path.join(self.prompt_dirs[0], f"{prompt_id}.md")
        
        os.makedirs(self.prompt_dirs[0], exist_ok=True)
        
        with open(prompt_file_path, 'w') as f:
            f.write(front_matter + prompt_body_content)
        
        # Load the prompt
        prompt = self.prompt_service.load_prompt(prompt_file_path)
        
        # Check if prompt was loaded correctly
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt.id, prompt_id)
        self.assertEqual(prompt.description, prompt_description)
        self.assertEqual(prompt.tags, prompt_tags)
        self.assertEqual(prompt.content, prompt_body_content)
        self.assertEqual(prompt.directory, self.prompt_dirs[0])

    def test_save_prompt_with_front_matter(self):
        """Test saving a prompt with front matter"""
        self.prompt_service.add_directory(self.prompt_dirs[0])
        prompt_id = "test_save_fm"
        description = "Description to save"
        tags = ["save", "fm"]
        content = "Content to save with front matter."
    
        self.prompt_service.create_prompt(
            id=prompt_id,
            content=content,
            directory=self.prompt_dirs[0],
            description=description,
            tags=tags
        )
    
        # Verify the file content
        prompt_file_path = os.path.join(self.prompt_dirs[0], f"{prompt_id}.md")
        self.assertTrue(os.path.exists(prompt_file_path))

        with open(prompt_file_path, 'r') as f:
            file_content = f.read()
        
        self.assertIn(f"description: {description}", file_content)
        self.assertIn(f"- {tags[0]}", file_content)
        self.assertIn(f"- {tags[1]}", file_content)
        self.assertIn(content, file_content)
        self.assertTrue(file_content.startswith("---"))

    # TODO: Add more tests for other PromptService methods like:
    # - load_all_prompts
    # - get_available_tags
    # - get_available_directories
    # - update_prompt_metadata (if it becomes separate from save_prompt)
    # - error handling for file operations (permissions, etc.)

# Tests for PromptService helper methods

@pytest.fixture
def service():
    """Provides a PromptService instance with auto_load=False and a temporary config file."""
    temp_dir = tempfile.mkdtemp()
    temp_config_file = os.path.join(temp_dir, "test_fixture_prompt_directories.json")
    
    config_patch = patch('src.services.prompt_service.PromptService.CONFIG_FILE', temp_config_file)
    config_patch.start()
    
    # Initialize service with no base_directories and auto_load=False
    # This ensures it starts clean and uses the patched (temporary) config file if it tries to load/save.
    ps = PromptService(base_directories=[], auto_load=False)
    
    yield ps # Provide the service instance to the test
    
    # Teardown: stop the patch and remove the temporary directory
    config_patch.stop()
    shutil.rmtree(temp_dir)

# Test cases for _normalize_path
# Each tuple: (input_path, expected_output_path)
normalize_path_test_cases = [
    ("/some/path/", "/some/path"),
    ("/some/path", "/some/path"),
    ("/some/./path/../other_path/", "/some/other_path"),
    ("/", "/"),
    ("relative/path/", "relative/path"),
    ("relative/path", "relative/path"),
    (".", "."), # os.path.normpath('.') is '.'
    ("..", ".."), # os.path.normpath('..') is '..'
    ("/some/path///", "/some/path"),
    ("//multiple/slashes/at/start", "/multiple/slashes/at/start"), # normpath handles this
    ("", "."), # os.path.normpath('') is '.'
    # Cases specific to os.sep if it's different (e.g., Windows)
    # For simplicity, assuming POSIX-like paths for these examples,
    # but os.path.normpath and os.sep handle OS-specificity.
    ("/a/b/c/../d/./e/", "/a/b/d/e"),
    ("a/b/../../c", "c"),
    # Test with root on windows, normpath makes it C:\ if C: is current drive
    # This test might be environment-dependent or need more sophisticated handling
    # For now, focusing on POSIX-style trailing slashes and normalization.
    pytest.param("C:\\path\\to\\file\\", "C:\\path\\to\\file", marks=pytest.mark.skipif(os.sep != '\\', reason="Windows specific path"))
]

@pytest.mark.parametrize("input_path, expected_path", normalize_path_test_cases)
def test_normalize_path(service, input_path, expected_path):
    # On Windows, normpath might convert forward slashes to backslashes.
    # To make tests consistent across OS for non-Windows specific cases,
    # we can replace os.sep with '/' in expected_path if we designed tests with '/'.
    # However, the current _normalize_path uses os.sep for rstrip, so results will be OS-native.
    # The key is that it normalizes and correctly handles trailing os.sep.

    # If running on Windows, and input_path uses '/', normpath will convert to '\\'.
    # The expected_path should reflect this for Windows environment if that's the case.
    # The provided posix style test cases will mostly work because normpath handles it.
    
    # For root path, os.path.normpath("/") is "/", and rstrip('/') on "/" when it's not the only char is the goal.
    # Our logic `normalized.endswith(os.sep) and normalized != os.sep` handles this.
    # If input is "/", normalized is "/", it doesn't end with os.sep (false), or it IS os.sep (true), so `and` is false. (Correction: it *does* end with os.sep)
    # If input is "/", normalized is "/", normalized.endswith(os.sep) is true. normalized != os.sep is false. So `and` is false. No rstrip. Correct.
    # If input is "/a/", normalized is "/a/", endswith is true. != os.sep is true. `and` is true. rstrip happens. Correct.

    # Special handling for empty string and current/parent dir, as normpath behavior is specific
    if input_path == "" and expected_path == ".":
        assert service._normalize_path(input_path) == expected_path
    elif input_path == "." and expected_path == ".":
        assert service._normalize_path(input_path) == expected_path
    elif input_path == ".." and expected_path == "..":
        assert service._normalize_path(input_path) == expected_path
    # For the root directory, ensure it remains just os.sep
    elif os.path.abspath(input_path) == os.path.abspath(expected_path) and len(expected_path) == 1 and expected_path == os.sep:
         assert service._normalize_path(input_path) == os.sep
    else:
        # For other cases, compare with a version of expected_path that is also os.path.normpath'd
        # to account for OS-specific representations, but ensure our trailing slash logic is the key difference.
        # The main thing we test beyond normpath is the trailing slash removal.
        processed_expected = os.path.normpath(expected_path)
        # If the original expected path didn't have a trailing slash, normpath shouldn't add one (unless it's root).
        # Our _normalize_path should match this normpath'd version.
        assert service._normalize_path(input_path) == processed_expected

# if __name__ == "__main__":
#     unittest.main() 