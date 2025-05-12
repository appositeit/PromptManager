"""
Tests for the prompt_service module focusing on composite prompt handling.
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone

from src.services.prompt_service import PromptService
from src.models.unified_prompt import Prompt


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
        self.assertIn("This is fragment 1", expanded)
        self.assertIn("fragment1", dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_multiple_expansions(self):
        """Test expansion of a template with multiple inclusions"""
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(self.template2.content)
        
        # Check the expansion
        self.assertIn("This is fragment 1", expanded)
        self.assertIn("This is fragment 2", expanded)
        self.assertEqual(len(dependencies), 2)
        self.assertIn("fragment1", dependencies)
        self.assertIn("fragment2", dependencies)
        self.assertEqual(len(warnings), 0)
        
    def test_nested_expansion(self):
        """Test expansion of a template with nested inclusions"""
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(self.complex_template.content)
        
        # Check the expansion
        self.assertIn("This is fragment 1", expanded)  # From nested_fragment -> fragment1
        self.assertIn("This is fragment 2", expanded)  # Direct inclusion
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
        
        # Should contain the content from the deepest level
        self.assertIn("Level 20 content with no inclusion", expanded)
        # Should have all levels as dependencies
        self.assertEqual(len(dependencies), 19)  # Only 19 because the last level is included but doesn't include anything else
        # Should have no warnings
        self.assertEqual(len(warnings), 0)
        
    def test_nonexistent_prompt_expansion(self):
        """Test expansion with a nonexistent prompt"""
        content = "Template with nonexistent inclusion: [[nonexistent_prompt]]"
        expanded, dependencies, warnings = self.prompt_service.expand_inclusions(content)
        
        # Check that expansion detected the nonexistent prompt
        self.assertIn("PROMPT NOT FOUND", expanded)
        self.assertEqual(len(dependencies), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Prompt not found", warnings[0])
        
    def test_find_prompts_by_inclusion(self):
        """Test finding prompts based on inclusion marker text"""
        # Find prompts that include fragment1
        results = self.prompt_service.find_prompts("[[fragment1]]")
        
        # Should find all prompts that directly include fragment1
        prompt_ids = [p.id for p in results]
        self.assertIn("nested_fragment", prompt_ids)
        self.assertIn("template1", prompt_ids)
        self.assertIn("template2", prompt_ids)
        
    def test_reload_with_changed_content(self):
        """Test reloading prompts with changed content affects is_composite status"""
        # Create a new prompt that is initially not composite
        non_composite = self.prompt_service.create_prompt(
            id="dynamic_test_prompt",
            content="This is a simple prompt with no inclusions.",
            directory=self.prompt_dirs[0]
        )
        
        # Verify it's not composite
        self.assertFalse(non_composite.is_composite)
        
        # Modify content to make it composite
        non_composite.content = "Now this includes something: [[fragment1]]"
        self.prompt_service.save_prompt(non_composite)
        
        # Get the path for direct reload
        prompt_path = non_composite.full_path
        
        # Reload from disk directly
        reloaded = self.prompt_service.load_prompt(prompt_path)
        
        # Check that it's now detected as composite
        self.assertTrue(reloaded.is_composite)
        
        # Make sure it appears in get_composite_prompts results
        composite_prompts = self.prompt_service.get_composite_prompts(self.prompt_dirs[0])
        fragment_composite_ids = [p.id for p in composite_prompts]
        self.assertIn("dynamic_test_prompt", fragment_composite_ids)
        
    def test_save_and_reload_composite_status(self):
        """Test that composite status is preserved through save and reload"""
        # Create a new prompt that is initially not composite
        non_composite = self.prompt_service.create_prompt(
            id="initially_non_composite",
            content="This is a simple prompt with no inclusions.",
            directory=self.prompt_dirs[0]
        )
        
        # Verify it's not composite
        self.assertFalse(non_composite.is_composite)
        
        # Update content to make it composite
        non_composite.content = "Now this includes something: [[fragment1]]"
        self.prompt_service.save_prompt(non_composite)
        
        # Reload from disk and verify it's now composite
        reloaded = self.prompt_service.load_prompt(non_composite.full_path)
        self.assertTrue(reloaded.is_composite)
        
        # Update again to make it non-composite
        reloaded.content = "Back to being simple with no inclusions."
        self.prompt_service.save_prompt(reloaded)
        
        # Reload and verify it's back to non-composite
        re_reloaded = self.prompt_service.load_prompt(reloaded.full_path)
        self.assertFalse(re_reloaded.is_composite)


if __name__ == "__main__":
    unittest.main()
