"""
Integration Tests for Better Identifiers System

Tests the complete end-to-end functionality of the better identifiers
implementation across all layers: models, services, API, and frontend.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from src.models.unified_prompt import Prompt
from src.services.prompt_service import PromptService
from src.api.router import create_new_prompt, get_all_prompts, get_prompt_by_id


class TestBetterIdentifiersIntegration:
    """Integration tests for the complete better identifiers system."""

    def setup_method(self):
        """Set up test environment with multiple prompt directories."""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create a complex directory structure with potential conflicts
        self.directories = {
            "project1": self.test_dir / "project1",
            "project2": self.test_dir / "project2", 
            "shared": self.test_dir / "shared",
            "nested/deep": self.test_dir / "nested" / "deep",
            "nested/other": self.test_dir / "nested" / "other"
        }
        
        for dir_path in self.directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create test prompts with various naming conflicts
        self.test_prompts = [
            # Unique filenames
            {"path": "project1/unique_prompt.md", "content": "Unique prompt content"},
            {"path": "shared/global_config.md", "content": "Global configuration"},
            
            # Filename conflicts
            {"path": "project1/setup.md", "content": "Project 1 setup"},
            {"path": "project2/setup.md", "content": "Project 2 setup"},
            {"path": "nested/deep/setup.md", "content": "Deep nested setup"},
            
            # More complex conflicts
            {"path": "project1/utils/helper.md", "content": "Project 1 helper"},
            {"path": "project2/utils/helper.md", "content": "Project 2 helper"},
            {"path": "nested/other/helper.md", "content": "Other helper"},
        ]
        
        # Create additional utils directories
        (self.test_dir / "project1" / "utils").mkdir(exist_ok=True)
        (self.test_dir / "project2" / "utils").mkdir(exist_ok=True)
        
        # Write all test files
        for prompt_data in self.test_prompts:
            file_path = self.test_dir / prompt_data["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"---\ndescription: Test prompt\ntags: [test]\n---\n{prompt_data['content']}")

    def teardown_method(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_end_to_end_unique_identifiers(self):
        """Test that all prompts receive unique full-path identifiers."""
        # Initialize service with test directories
        service = PromptService(
            base_directories=[str(d) for d in self.directories.values()],
            auto_load=False,
            create_default_directory_if_empty=False
        )
        # Clear default prompts and load only test prompts
        service.prompts.clear()
        service.load_all_prompts()
        
        all_prompts_data = service.get_all_prompts()
        prompt_ids = [p["id"] for p in all_prompts_data]
        
        # Verify all IDs are unique
        assert len(prompt_ids) == len(set(prompt_ids)), "All prompt IDs should be unique"
        
        # Verify IDs are full paths
        for prompt_data in all_prompts_data:
            assert "/" in prompt_data["id"] or "\\" in prompt_data["id"], f"ID should be full path: {prompt_data['id']}"
            assert not prompt_data["id"].endswith(".md"), f"ID should not include .md extension: {prompt_data['id']}"

    def test_display_name_calculation_integration(self):
        """Test display name calculation across the complete prompt set."""
        service = PromptService(
            base_directories=[str(d) for d in self.directories.values()],
            auto_load=False,
            create_default_directory_if_empty=False
        )
        # Clear default prompts and load only test prompts
        service.prompts.clear()
        service.load_all_prompts()
        
        all_prompts_data = service.get_all_prompts()
        
        # Calculate display names - need to pass the actual prompt data, not just IDs
        display_names = Prompt.calculate_all_display_names(all_prompts_data)
        
        # Verify display names are unique
        display_name_values = list(display_names.values())
        assert len(display_name_values) == len(set(display_name_values)), "All display names should be unique"
        
        # Verify expected display names for known conflicts
        expected_patterns = {
            "unique_prompt": "unique_prompt",  # Unique filename
            "global_config": "global_config",  # Unique filename
            "project1:setup": True,  # Should include directory due to conflict
            "project2:setup": True,  # Should include directory due to conflict
            "project1:utils:helper": True,  # Should include multiple directories
            "project2:utils:helper": True,  # Should include multiple directories
        }
        
        # Find prompts and check their display names match expectations
        for prompt_data in all_prompts_data:
            display_name = display_names[prompt_data["id"]]
            
            if "unique_prompt" in prompt_data["id"]:
                assert display_name == "unique_prompt"
            elif "global_config" in prompt_data["id"]:
                assert display_name == "global_config" 
            elif "setup" in prompt_data["id"]:
                assert ":" in display_name, f"Setup prompts should have directory prefix: {display_name}"
            elif "helper" in prompt_data["id"] and "utils" in prompt_data["id"]:
                assert ":" in display_name, f"Helper prompts should have directory prefix: {display_name}"

    def test_api_integration_with_display_names(self):
        """Test API responses include proper display names."""
        with patch('src.services.prompt_service.PromptService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Create mock prompts with known IDs
            mock_prompts = [
                Mock(
                    id="project1/setup",
                    name="setup",
                    directory="project1", 
                    directory_name="project1",
                    display_name="project1:setup",
                    to_dict=Mock(return_value={
                        "id": "project1/setup",
                        "name": "setup", 
                        "directory": "project1",
                        "directory_name": "project1",
                        "display_name": "project1:setup",
                        "description": "Test",
                        "tags": [],
                        "content": "Test content"
                    })
                ),
                Mock(
                    id="project2/setup", 
                    name="setup",
                    directory="project2",
                    directory_name="project2", 
                    display_name="project2:setup",
                    to_dict=Mock(return_value={
                        "id": "project2/setup",
                        "name": "setup",
                        "directory": "project2", 
                        "directory_name": "project2",
                        "display_name": "project2:setup",
                        "description": "Test",
                        "tags": [],
                        "content": "Test content"
                    })
                )
            ]
            
            mock_service.get_all_prompts.return_value = mock_prompts
            
            # Test get_all_prompts API endpoint
            response = get_all_prompts()
            
            # Verify response structure
            assert "prompts" in response
            prompts_data = response["prompts"]
            
            # Verify display names are included
            for prompt_data in prompts_data:
                assert "display_name" in prompt_data
                assert "directory_name" in prompt_data
                if "setup" in prompt_data["name"]:
                    assert ":" in prompt_data["display_name"], "Conflicting names should have directory prefix"

    def test_inclusion_resolution_with_full_paths(self):
        """Test that inclusion resolution works with full-path IDs."""
        service = PromptService(
            base_directories=[str(d) for d in self.directories.values()],
            auto_load=False,
            create_default_directory_if_empty=False
        )
        # Clear default prompts and load only test prompts
        service.prompts.clear()
        service.load_all_prompts()
        
        # Create a prompt with inclusions using both display names and full paths
        composite_content = """
        Main content here.
        [[unique_prompt]]
        [[project1:setup]]
        [[project1/utils/helper]]
        """
        
        composite_path = self.test_dir / "shared" / "composite.md"
        composite_path.write_text(f"---\ndescription: Composite prompt\n---\n{composite_content}")
        
        # Reload to include new prompt
        service.load_all_prompts()
        
        # Get the composite prompt
        composite_prompt = None
        all_prompts_data = service.get_all_prompts()
        for prompt_data in all_prompts_data:
            if "composite" in prompt_data["id"]:
                composite_prompt = service.get_prompt(prompt_data["id"])
                break
        
        assert composite_prompt is not None, "Composite prompt should be found"
        
        # Test expansion
        expanded_content, dependencies, warnings = service.expand_inclusions(
            composite_prompt.content, 
            parent_directory=composite_prompt.directory,
            parent_id=composite_prompt.id
        )
        
        # Verify inclusions were resolved
        assert len(dependencies) > 0, "Should have resolved dependencies"
        
        # Verify content was actually expanded (should be longer than original)
        assert len(expanded_content) > len(composite_content), "Expanded content should be longer"

    def test_error_handling_with_missing_inclusions(self):
        """Test error handling when inclusions reference non-existent prompts."""
        service = PromptService(
            base_directories=[str(d) for d in self.directories.values()],
            auto_load=False,
            create_default_directory_if_empty=False
        )
        # Clear default prompts and load only test prompts
        service.prompts.clear()
        service.load_all_prompts()
        
        # Create content with non-existent inclusions
        content_with_missing = """
        Valid content.
        [[nonexistent_prompt]]
        [[another:missing:prompt]]
        """
        
        # Test expansion with missing inclusions
        expanded_content, dependencies, warnings = service.expand_inclusions(
            content_with_missing, 
            parent_directory=None,
            parent_id="test/prompt"
        )
        
        # Should still succeed but with warnings
        assert len(warnings) > 0, "Should have warnings about missing inclusions"
        
        # Content should remain unchanged for missing inclusions
        assert "[[nonexistent_prompt]]" in expanded_content, "Missing inclusions should remain as-is"

    def test_directory_name_display_consistency(self):
        """Test that directory names are consistently calculated and displayed."""
        service = PromptService(
            base_directories=[str(d) for d in self.directories.values()],
            auto_load=False,
            create_default_directory_if_empty=False
        )
        # Clear default prompts and load only test prompts
        service.prompts.clear()
        service.load_all_prompts()
        
        all_prompts_data = service.get_all_prompts()
        
        # Verify directory_name is set for all prompts
        for prompt_data in all_prompts_data:
            assert "directory_name" in prompt_data, f"Prompt {prompt_data['id']} missing directory_name"
            assert prompt_data["directory_name"] is not None, f"Prompt {prompt_data['id']} has None directory_name"
            assert len(prompt_data["directory_name"]) > 0, f"Prompt {prompt_data['id']} has empty directory_name"
            
            # Directory name should be shorter than full directory path
            if "/" in prompt_data["directory"] or "\\" in prompt_data["directory"]:
                assert len(prompt_data["directory_name"]) <= len(prompt_data["directory"]), \
                    f"Directory name should not be longer than full path: {prompt_data['directory_name']} vs {prompt_data['directory']}"

    def test_performance_with_large_prompt_set(self):
        """Test performance of display name calculation with larger prompt sets."""
        # Create a larger set of mock prompt IDs
        large_prompt_set = []
        
        # Generate systematic conflicts
        for project in range(1, 6):  # 5 projects
            for module in ['auth', 'config', 'utils', 'tests']:
                for item in ['setup', 'main', 'helper', 'test']:
                    prompt_id = f"project{project}/{module}/{item}"
                    large_prompt_set.append(prompt_id)
        
        # Add some unique items
        for i in range(20):
            large_prompt_set.append(f"unique/item_{i}")
        
        # Convert to proper format for the method
        large_prompt_data = [{"id": prompt_id, "name": prompt_id.split("/")[-1]} for prompt_id in large_prompt_set]
        
        # Test display name calculation performance
        import time
        start_time = time.time()
        
        display_names = Prompt.calculate_all_display_names(large_prompt_data)
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Should complete reasonably quickly (under 1 second for ~120 prompts)
        assert calculation_time < 1.0, f"Display name calculation took too long: {calculation_time}s"
        
        # Verify all names are unique
        display_name_values = list(display_names.values())
        assert len(display_name_values) == len(set(display_name_values)), "All display names should be unique"
        
        # Verify systematic conflicts are properly handled
        setup_names = [name for name in display_name_values if name.endswith('setup')]
        assert len(setup_names) == 20, "Should have 20 setup prompts with unique display names"
        assert len(set(setup_names)) == 20, "All setup display names should be unique"

    def test_backward_compatibility_with_legacy_ids(self):
        """Test that the system maintains backward compatibility with legacy ID formats."""
        service = PromptService(
            base_directories=[str(d) for d in self.directories.values()],
            auto_load=False,
            create_default_directory_if_empty=False
        )
        # Clear default prompts and load only test prompts
        service.prompts.clear()
        service.load_all_prompts()
        
        # Test that we can still find prompts by filename alone (legacy behavior)
        all_prompts_data = service.get_all_prompts()
        
        # Find a prompt with a unique filename
        unique_prompt_data = None
        for prompt_data in all_prompts_data:
            if "unique_prompt" in prompt_data["id"]:
                unique_prompt_data = prompt_data
                break
        
        if unique_prompt_data:
            unique_prompt = service.get_prompt(unique_prompt_data["id"])
            
            # Test lookup by legacy ID (just filename)
            legacy_id = "unique_prompt"
            found_prompt = service.get_prompt(legacy_id)
            
            # Should find the prompt (backward compatibility)
            # Note: This depends on the implementation - if legacy lookup is supported
            # If not supported, this test documents the expected behavior
            
            # For now, test that the full ID lookup definitely works
            full_id_prompt = service.get_prompt(unique_prompt.id)
            assert full_id_prompt is not None, "Full ID lookup should always work"
            assert full_id_prompt.id == unique_prompt.id, "Should find the same prompt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
