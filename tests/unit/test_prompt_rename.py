"""
Unit tests for prompt renaming functionality within the PromptService.

These tests verify the `rename_prompt` method of the PromptService,
ensuring that prompts are correctly renamed on the filesystem and
within the service's internal state. It covers scenarios such as
basic renaming, renaming with content updates, and error handling
when a target prompt ID already exists.

Modules/Classes Tested:
- src.services.prompt_service.PromptService (methods: create_prompt, rename_prompt, get_prompt)
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch

# Import the PromptService for testing
from src.services.prompt_service import PromptService


class TestPromptRename(unittest.TestCase):
    # Removed original docstring to avoid duplication with the module-level one

    def setUp(self):
        """Set up temporary test directories and patch config file."""
        self.test_dir = tempfile.mkdtemp()
        
        # Patch CONFIG_FILE to use a temporary file for this test suite
        self.config_file_patch = patch('src.services.prompt_service.PromptService.CONFIG_FILE', 
                                       os.path.join(self.test_dir, "test_rename_prompt_directories.json"))
        self.mock_config_file = self.config_file_patch.start()
        
        # Initialize service with no base_directories and auto_load=False
        # This ensures it starts clean and uses the patched (temporary) config file.
        self.prompt_service = PromptService(base_directories=[], auto_load=False)
        # Now add the temporary directory to the service that uses the temporary config
        self.prompt_service.add_directory(self.test_dir)

    def tearDown(self):
        """Clean up temporary test directories and stop patch."""
        self.config_file_patch.stop() # Stop the patch first
        shutil.rmtree(self.test_dir)

    def test_rename_prompt(self):
        """Test renaming a prompt."""
        # Create a test prompt
        old_id = "test_prompt"
        content = "# Test Prompt\n\nThis is a test prompt."
        description = "A test prompt"
        tags = ["test", "sample"]

        # Create the prompt
        prompt = self.prompt_service.create_prompt(
            id=old_id,
            content=content,
            directory=self.test_dir,
            description=description,
            tags=tags
        )

        # Verify the prompt was created correctly
        self.assertEqual(prompt.id, old_id)
        self.assertEqual(prompt.content, content)
        self.assertEqual(prompt.description, description)
        self.assertEqual(prompt.tags, tags)

        # Verify the file was created
        old_file_path = os.path.join(self.test_dir, f"{old_id}.md")
        self.assertTrue(os.path.exists(old_file_path))

        # Rename the prompt
        new_id = "renamed_prompt"
        success = self.prompt_service.rename_prompt(
            old_id=old_id,
            new_id=new_id
        )

        # Verify the rename was successful
        self.assertTrue(success)

        # Verify the old file no longer exists
        self.assertFalse(os.path.exists(old_file_path))

        # Verify the new file exists
        new_file_path = os.path.join(self.test_dir, f"{new_id}.md")
        self.assertTrue(os.path.exists(new_file_path))

        # Verify the prompt can be retrieved by the new ID
        renamed_prompt = self.prompt_service.get_prompt(new_id)
        self.assertIsNotNone(renamed_prompt)
        self.assertEqual(renamed_prompt.id, new_id)
        self.assertEqual(renamed_prompt.content, content)
        self.assertEqual(renamed_prompt.description, description)
        self.assertEqual(renamed_prompt.tags, tags)

        # Verify the prompt can no longer be retrieved by the old ID
        old_prompt = self.prompt_service.get_prompt(old_id)
        self.assertIsNone(old_prompt)

    def test_rename_prompt_with_content_update(self):
        """Test renaming a prompt with content and metadata updates."""
        # Create a test prompt
        old_id = "test_prompt"
        original_content = "# Test Prompt\n\nThis is a test prompt."
        original_description = "A test prompt"
        original_tags = ["test", "sample"]

        # Create the prompt
        self.prompt_service.create_prompt(
            id=old_id,
            content=original_content,
            directory=self.test_dir,
            description=original_description,
            tags=original_tags
        )

        # New data for rename
        new_id = "renamed_prompt"
        updated_content = "# Renamed Prompt\n\nThis prompt has been renamed."
        updated_description = "A renamed prompt"
        updated_tags = ["renamed", "updated"]

        # Rename the prompt with updates
        success = self.prompt_service.rename_prompt(
            old_id=old_id,
            new_id=new_id,
            content=updated_content,
            description=updated_description,
            tags=updated_tags
        )

        # Verify the rename was successful
        self.assertTrue(success)

        # Verify the updated prompt has the correct data
        renamed_prompt = self.prompt_service.get_prompt(new_id)
        self.assertIsNotNone(renamed_prompt)
        self.assertEqual(renamed_prompt.id, new_id)
        self.assertEqual(renamed_prompt.content, updated_content)
        self.assertEqual(renamed_prompt.description, updated_description)
        self.assertEqual(renamed_prompt.tags, updated_tags)

    def test_rename_prompt_error_existing(self):
        """Test error handling when renaming to a prompt ID that already exists."""
        # Create two test prompts
        prompt1_id = "prompt1"
        prompt2_id = "prompt2"

        # Create the prompts
        self.prompt_service.create_prompt(
            id=prompt1_id,
            content="Prompt 1",
            directory=self.test_dir
        )

        self.prompt_service.create_prompt(
            id=prompt2_id,
            content="Prompt 2",
            directory=self.test_dir
        )

        # Try to rename prompt1 to prompt2 (which already exists)
        success = self.prompt_service.rename_prompt(
            old_id=prompt1_id,
            new_id=prompt2_id
        )

        # Verify the rename failed
        self.assertFalse(success)

        # Verify both original prompts still exist
        self.assertIsNotNone(self.prompt_service.get_prompt(prompt1_id))
        self.assertIsNotNone(self.prompt_service.get_prompt(prompt2_id))


# if __name__ == "__main__":
#     unittest.main() 