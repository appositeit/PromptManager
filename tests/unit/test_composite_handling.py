"""
Unit tests for composite prompt handling in the PromptService.

These tests verify the functionality of the PromptService related to
detecting, expanding, and managing prompts that include other prompts
(composite prompts). This includes testing for various inclusion
patterns, circular dependencies, and deep nesting.

Modules/Classes Tested:
- src.services.prompt_service.PromptService
- src.models.unified_prompt.Prompt (specifically its composite-related attributes)
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.services.prompt_service import PromptService


class TestPromptServiceComposites(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test prompt directories
        self.prompt_dirs = [
            os.path.join(self.test_dir, "fragments"),
            os.path.join(self.test_dir, "templates"),
        ]
        
        # Create the directories
        for dir_path in self.prompt_dirs:
            os.makedirs(dir_path)
            
        # Create a test prompt service
        # Patch CONFIG_FILE to use a temporary file for this test suite
        self.config_file_patch = patch('src.services.prompt_service.PromptService.CONFIG_FILE', 
                                       os.path.join(self.test_dir, "test_composite_prompt_directories.json"))
        self.mock_config_file = self.config_file_patch.start()
        
        self.prompt_service = PromptService(base_directories=self.prompt_dirs, auto_load=False)
        
        # Add directories to the service
        for dir_path in self.prompt_dirs:
            self.prompt_service.add_directory(dir_path)
            
        # Sample prompts for testing with varying levels of complexity
        self.create_test_prompts()
        
    def create_test_prompts(self):
        """Create a set of test prompts with various inclusion patterns"""
        # Create simple fragments
        self.fragment1 = self.prompt_service.create_prompt(
            id="fragment1",
            content="This is fragment 1.",
            directory=self.prompt_dirs[0],
            description="A simple fragment",
            tags=["fragment", "simple"]
        )
        
        self.fragment2 = self.prompt_service.create_prompt(
            id="fragment2",
            content="This is fragment 2.",
            directory=self.prompt_dirs[0],
            description="Another simple fragment",
            tags=["fragment", "simple"]
        )
        
        # Create a fragment that includes another fragment
        self.nested_fragment = self.prompt_service.create_prompt(
            id="nested_fragment",
            content="This is a nested fragment: [[fragment1]]",
            directory=self.prompt_dirs[0],
            description="A fragment that includes another fragment",
            tags=["fragment", "nested"]
        )
        
        # Create simple templates
        self.template1 = self.prompt_service.create_prompt(
            id="template1",
            content="Template with one inclusion: [[fragment1]]",
            directory=self.prompt_dirs[1],
            description="A simple template",
            tags=["template", "simple"]
        )
        
        self.template2 = self.prompt_service.create_prompt(
            id="template2",
            content="Template with multiple inclusions: [[fragment1]] and [[fragment2]]",
            directory=self.prompt_dirs[1],
            description="A template with multiple inclusions",
            tags=["template", "multiple"]
        )
        
        # Create a complex template with nested inclusions
        self.complex_template = self.prompt_service.create_prompt(
            id="complex_template",
            content="Complex template with nested inclusions: [[nested_fragment]] and [[fragment2]]",
            directory=self.prompt_dirs[1],
            description="A complex template with nested inclusions",
            tags=["template", "complex"]
        )
        
        # Create a template with self-reference (circular dependency)
        self.circular_template = self.prompt_service.create_prompt(
            id="circular_template",
            content="Template with circular reference: [[circular_template]]",
            directory=self.prompt_dirs[1],
            description="A template with a circular reference",
            tags=["template", "circular"]
        )
        
        # Create a template with mutual circular dependency
        self.mutual_circular1 = self.prompt_service.create_prompt(
            id="mutual_circular1",
            content="Template with mutual circular reference: [[mutual_circular2]]",
            directory=self.prompt_dirs[1],
            description="A template with a mutual circular reference",
            tags=["template", "circular"]
        )
        
        self.mutual_circular2 = self.prompt_service.create_prompt(
            id="mutual_circular2",
            content="Template with mutual circular reference: [[mutual_circular1]]",
            directory=self.prompt_dirs[1],
            description="A template with a mutual circular reference",
            tags=["template", "circular"]
        )
        
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        # Stop the patch
        self.config_file_patch.stop()
        
    def test_is_composite_detection(self):
        """Test detection of composite prompts"""
        # Test simple fragment (not composite)
        self.assertFalse(self.fragment1.is_composite)
        
        # Test nested fragment (is composite)
        self.assertTrue(self.nested_fragment.is_composite)
        
        # Test simple template (is composite)
        self.assertTrue(self.template1.is_composite)
        
        # Test complex template (is composite)
        self.assertTrue(self.complex_template.is_composite)
        
    def test_get_composite_prompts(self):
        """Test retrieving all composite prompts"""
        composite_prompts = self.prompt_service.get_composite_prompts()
        
        # Check that all composite prompts were retrieved
        # Note: The exact count might vary depending on the test environment and what prompts are loaded
        self.assertGreaterEqual(len(composite_prompts), 5)  # At minimum, all templates and the nested fragment
        
        # Check that specific prompts are in the results
        prompt_ids = [p.id for p in composite_prompts]
        self.assertIn("nested_fragment", prompt_ids)
        self.assertIn("template1", prompt_ids)
        self.assertIn("template2", prompt_ids)
        self.assertIn("complex_template", prompt_ids)
        
        # Test filtering by directory
        fragments_dir_composites = self.prompt_service.get_composite_prompts(self.prompt_dirs[0])
        self.assertGreaterEqual(len(fragments_dir_composites), 1)  # At least the nested fragment
        self.assertTrue(any(p.id == "nested_fragment" for p in fragments_dir_composites))
        
        templates_dir_composites = self.prompt_service.get_composite_prompts(self.prompt_dirs[1])
        # Should have at least the 5 templates we created, but might have more
        self.assertGreaterEqual(len(templates_dir_composites), 5)
        
    def test_simple_expansion(self):
        """Test expansion of a simple template with one inclusion"""
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(self.template1.content)
        
        # Check the expansion
        self.assertIn("This is fragment 1.", expanded)
        self.assertIn("fragment1", dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_multiple_expansions(self):
        """Test expansion of a template with multiple inclusions"""
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(self.template2.content)
        
        # Check the expansion
        self.assertIn("This is fragment 1.", expanded)
        self.assertIn("This is fragment 2.", expanded)
        self.assertEqual(len(dependencies), 2)
        self.assertIn("fragment1", dependencies)
        self.assertIn("fragment2", dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_nested_expansion(self):
        """Test expansion of a template with nested inclusions"""
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(self.complex_template.content)
        
        # Check the expansion
        self.assertIn("This is fragment 1.", expanded)  # From nested_fragment -> fragment1
        self.assertIn("This is fragment 2.", expanded)  # Direct inclusion
        self.assertEqual(len(dependencies), 3)
        self.assertIn("nested_fragment", dependencies)
        self.assertIn("fragment1", dependencies)
        self.assertIn("fragment2", dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_circular_expansion(self):
        """Test expansion of a template with a circular reference"""
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(self.circular_template.content)
        
        # Check that expansion detected the circular reference
        self.assertIn("CIRCULAR DEPENDENCY", expanded)
        self.assertIn("circular_template", dependencies)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Circular dependency detected", warnings[0])
        
    def test_mutual_circular_expansion(self):
        """Test expansion of templates with mutual circular references"""
        expanded1, dependencies1, warnings1 = self.prompt_service.expand_inclusions(self.mutual_circular1.content)
        
        # Check that expansion detected the circular reference
        self.assertIn("CIRCULAR DEPENDENCY", expanded1)
        self.assertIn("mutual_circular2", dependencies1)
        self.assertEqual(len(warnings1), 1)
        self.assertIn("Circular dependency detected", warnings1[0])
        
        expanded2, dependencies2, warnings2 = self.prompt_service.expand_inclusions(self.mutual_circular2.content)
        self.assertIn("CIRCULAR DEPENDENCY", expanded2)
        self.assertEqual(len(warnings2), 1)
        
    def test_deep_nesting(self):
        """Test handling of deeply nested templates without recursion depth limits"""
        # Create deeply nested templates
        deep_prompts = []
        
        # Create templates with deep nesting (20 levels)
        for i in range(1, 21):
            current_id = f"deep{i}"
            if i < 20:
                # For levels 1-19, each one includes the next level
                next_id = f"deep{i+1}"
                content = f"Level {i} content with inclusion: [[{next_id}]]"
            else:
                # The last level (20) doesn't include anything
                content = f"Level {i} content with no inclusion"
                
            prompt = self.prompt_service.create_prompt(
                id=current_id,
                content=content,
                directory=self.prompt_dirs[1],
                description=f"Level {i} template",
                tags=["template", "deep"]
            )
            deep_prompts.append(prompt)
            
        # Expand the top-level template - should work regardless of depth
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(deep_prompts[0].content)
        
        # Debug output when test fails
        print(f"Expanded content: {expanded}")
        print(f"Warnings: {warnings}")
        self.assertNotIn("CIRCULAR DEPENDENCY", expanded, "Deep nesting should not trigger circular dependency error")
        self.assertIn("Level 20 content with no inclusion", expanded, "Deeply nested content not found in expansion")
        self.assertEqual(len(warnings), 0, "Warnings found during deep nesting expansion")

    def test_nonexistent_prompt_expansion(self):
        """Test expansion of a template with a non-existent inclusion"""
        content_with_nonexistent = "This prompt includes [[non_existent_prompt]] which does not exist."
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(content_with_nonexistent)
        
        self.assertIn("[[PROMPT NOT FOUND: non_existent_prompt]]", expanded)
        self.assertIn("non_existent_prompt", dependencies)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Prompt 'non_existent_prompt' not found", warnings[0])

    def test_find_prompts_by_inclusion(self):
        """Test finding prompts that include a specific prompt"""
        # The complex_template includes nested_fragment, which includes fragment1
        # The template1 includes fragment1
        # The template2 includes fragment1 and fragment2
        including_fragment1 = self.prompt_service.find_prompts_by_inclusion("fragment1")
        ids_including_fragment1 = {p.id for p in including_fragment1}
        
        self.assertIn("nested_fragment", ids_including_fragment1)
        self.assertIn("template1", ids_including_fragment1)
        self.assertIn("template2", ids_including_fragment1)
        self.assertIn("complex_template", ids_including_fragment1) # complex_template -> nested_fragment -> fragment1
                                                                 # So, complex_template should also be listed.

    def test_reload_with_changed_content(self):
        """Test that reloading a prompt correctly updates its composite status and content."""
        prompt_id = "reload_test_prompt"
        original_content = "Original content, not composite."
        
        # Create the initial prompt
        prompt = self.prompt_service.create_prompt(
            id=prompt_id,
            content=original_content,
            directory=self.prompt_dirs[0]
        )
        self.assertFalse(prompt.is_composite, "Initial prompt should not be composite")

        # Manually change the file content to make it composite
        new_content = "New content with inclusion: [[fragment1]]"
        with open(prompt.full_path, "w") as f:
            f.write(new_content)
        
        # Reload the specific prompt
        reloaded_prompt = self.prompt_service.load_prompt(prompt.full_path)
        self.assertIsNotNone(reloaded_prompt, "Failed to reload prompt")
        self.assertEqual(reloaded_prompt.content, new_content, "Reloaded prompt content mismatch")
        self.assertTrue(reloaded_prompt.is_composite, "Reloaded prompt should be composite")

        # Check the prompt from the service's cache/list after a full reload
        self.prompt_service.load_all_prompts() # This should pick up the change
        service_prompt = self.prompt_service.get_prompt(prompt_id)
        self.assertIsNotNone(service_prompt, "Prompt not found in service after full reload")
        self.assertEqual(service_prompt.content, new_content, "Service prompt content mismatch after full reload")
        self.assertTrue(service_prompt.is_composite, "Service prompt should be composite after full reload")

    def test_save_and_reload_composite_status(self):
        """Test that is_composite status is correctly determined after save and reload."""
        prompt_id = "save_reload_composite"
        composite_content = "This is a composite prompt: [[fragment1]]"

        # Create and save a composite prompt
        self.prompt_service.create_prompt(
            id=prompt_id,
            content=composite_content,
            directory=self.prompt_dirs[0],
            description="Test",
            tags=[]
        )
        
        # Clear the service's cache and reload
        self.prompt_service.prompts = {}
        
        # Find the PromptDirectory object corresponding to self.prompt_dirs[0]
        target_dir_path = self.prompt_dirs[0]
        directory_to_load = None
        for d_obj in self.prompt_service.directories:
            if d_obj.path == target_dir_path:
                directory_to_load = d_obj
                break
        
        if not directory_to_load:
            self.fail(f"Could not find PromptDirectory object for path: {target_dir_path}")
            
        self.prompt_service.load_prompts_from_directory(directory_to_load)
        
        loaded_prompt = self.prompt_service.get_prompt(prompt_id)
        self.assertIsNotNone(loaded_prompt, "Prompt not loaded after save and reload")
        self.assertTrue(loaded_prompt.is_composite, "Loaded prompt should be composite")
        self.assertEqual(loaded_prompt.content, composite_content)

# if __name__ == "__main__":
#     unittest.main() 