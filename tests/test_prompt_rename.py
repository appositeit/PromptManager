import unittest
import os
import tempfile
import shutil
from pathlib import Path

# Import the PromptService for testing
from src.services.prompt_service import PromptService
from src.models.unified_prompt import Prompt


class TestPromptRename(unittest.TestCase):
    """Test the prompt rename functionality."""

    def setUp(self):
        """Set up temporary test directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_service = PromptService(auto_load=False)
        self.prompt_service.add_directory(self.temp_dir)

    def tearDown(self):
        """Clean up temporary test directories."""
        shutil.rmtree(self.temp_dir)

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
            directory=self.temp_dir,
            description=description,
            tags=tags
        )

        # Verify the prompt was created correctly
        self.assertEqual(prompt.id, old_id)
        self.assertEqual(prompt.content, content)
        self.assertEqual(prompt.description, description)
        self.assertEqual(prompt.tags, tags)

        # Verify the file was created
        old_file_path = os.path.join(self.temp_dir, f"{old_id}.md")
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
        new_file_path = os.path.join(self.temp_dir, f"{new_id}.md")
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
            directory=self.temp_dir,
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
            directory=self.temp_dir
        )

        self.prompt_service.create_prompt(
            id=prompt2_id,
            content="Prompt 2",
            directory=self.temp_dir
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


if __name__ == "__main__":
    unittest.main()
