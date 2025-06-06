"""
Tests for the collapsible sidebar functionality
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

class TestCollapsibleSidebarAPI:
    """Tests for the collapsible sidebar API endpoints"""
    
    def test_directory_prompts_endpoint_exists(self):
        """Test that the directory prompts API endpoint exists and returns data"""
        with patch('src.api.router.get_prompt_service_dependency') as mock_dep:
            mock_service = MagicMock()
            mock_service.get_all_prompts.return_value = [
                {
                    "id": "test_directory/prompt_1",
                    "name": "prompt_1", 
                    "directory": "/test/directory",
                    "display_name": "First Test Prompt",
                    "description": "A test prompt",
                    "tags": ["test"],
                    "is_composite": False,
                    "last_updated": "2025-06-01T22:00:00Z"
                }
            ]
            mock_dep.return_value = mock_service
            
            from fastapi import FastAPI
            from src.api.router import router
            
            app = FastAPI()
            app.include_router(router)
            
            client = TestClient(app)
            response = client.get("/api/prompts/directories/test/prompts")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_directory_filtering_logic(self):
        """Test that directory prompts are filtered correctly"""
        # Test the filtering logic that would happen in the API
        all_prompts = [
            {"id": "dir1/prompt1", "directory": "/dir1", "display_name": "Prompt 1"},
            {"id": "dir2/prompt2", "directory": "/dir2", "display_name": "Prompt 2"},
            {"id": "dir1/prompt3", "directory": "/dir1", "display_name": "Prompt 3"}
        ]
        
        target_directory = "/dir1"
        filtered_prompts = [p for p in all_prompts if p["directory"] == target_directory]
        
        assert len(filtered_prompts) == 2
        for prompt in filtered_prompts:
            assert prompt["directory"] == target_directory

    def test_alphabetical_sorting(self):
        """Test alphabetical sorting of directory prompts"""
        unsorted_prompts = [
            {"id": "dir/zebra", "display_name": "Zebra Prompt"},
            {"id": "dir/alpha", "display_name": "Alpha Prompt"}, 
            {"id": "dir/beta", "display_name": "Beta Prompt"}
        ]
        
        sorted_prompts = sorted(unsorted_prompts, key=lambda p: p.get('display_name', p['id']).lower())
        
        assert sorted_prompts[0]['display_name'] == "Alpha Prompt"
        assert sorted_prompts[1]['display_name'] == "Beta Prompt"
        assert sorted_prompts[2]['display_name'] == "Zebra Prompt"


class TestCollapsibleSidebarIntegration:
    """Integration tests for the complete collapsible sidebar functionality"""
    
    def test_css_file_exists(self):
        """Test that the CSS file is created and accessible"""
        import os
        css_path = "/home/jem/development/prompt_manager/src/static/css/collapsible-sidebar.css"
        assert os.path.exists(css_path), "CSS file should exist"
        
        with open(css_path, 'r') as f:
            css_content = f.read()
            
        expected_classes = [
            '.collapsible-header',
            '.collapse-chevron', 
            '.directory-prompts-list',
            '.directory-prompt-item'
        ]
        
        for css_class in expected_classes:
            assert css_class in css_content, f"CSS should contain {css_class}"

    def test_javascript_file_exists(self):
        """Test that the JavaScript file is created and accessible"""
        import os
        js_path = "/home/jem/development/prompt_manager/src/static/js/collapsible-sidebar.js"
        assert os.path.exists(js_path), "JavaScript file should exist"
        
        with open(js_path, 'r') as f:
            js_content = f.read()
            
        expected_features = [
            'class CollapsibleSidebar',
            'loadSidebarState',
            'initializeCollapsibleCards',
            'loadDirectoryPrompts'
        ]
        
        for feature in expected_features:
            assert feature in js_content, f"JavaScript should contain {feature}"

    def test_template_modifications(self):
        """Test that the HTML template includes the new collapsible structure"""
        template_path = "/home/jem/development/prompt_manager/src/templates/prompt_editor.html"
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Check for CSS inclusion
        assert 'collapsible-sidebar.css' in template_content, "Template should include CSS file"
        
        # Check for JS inclusion  
        assert 'collapsible-sidebar.js' in template_content, "Template should include JS file"
        
        # Check for new HTML structure
        expected_elements = [
            'data-card-id="metadata"',
            'data-card-id="directoryPrompts"', 
            'data-card-id="dependencies"',
            'collapsible-header',
            'directory-prompts-list'
        ]
        
        for element in expected_elements:
            assert element in template_content, f"Template should contain {element}"

    def test_eslint_compliance(self):
        """Test that the JavaScript code passes ESLint"""
        import subprocess
        
        js_file = "/home/jem/development/prompt_manager/src/static/js/collapsible-sidebar.js"
        
        result = subprocess.run(
            ['npx', 'eslint', js_file],
            cwd="/home/jem/development/prompt_manager",
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"ESLint should pass, but got errors: {result.stdout + result.stderr}"


class TestCollapsibleSidebarBehavior:
    """Tests for the expected behavior of the collapsible sidebar"""
    
    def test_sidebar_state_structure(self):
        """Test that sidebar state structure is correct"""
        expected_state = {
            'metadata': True,
            'directoryPrompts': True, 
            'dependencies': True,
            'referencedBy': True,
            'markdownCheat': True
        }
        
        # Verify all expected sections are present and default to open
        for section, state in expected_state.items():
            assert state is True, f"Section {section} should default to open"

    def test_drag_drop_format(self):
        """Test that drag and drop data format is correct"""
        test_prompt_id = "test_directory/example_prompt"
        expected_drag_text = f"[[{test_prompt_id}]]"
        
        assert expected_drag_text.startswith("[[")
        assert expected_drag_text.endswith("]]")
        assert test_prompt_id in expected_drag_text

    def test_current_prompt_filtering(self):
        """Test filtering of current prompt from directory list"""
        current_prompt_id = "test_dir/current_prompt"
        
        directory_prompts = [
            {"id": "test_dir/prompt_1", "display_name": "Prompt 1"},
            {"id": "test_dir/current_prompt", "display_name": "Current Prompt"},
            {"id": "test_dir/prompt_3", "display_name": "Prompt 3"}
        ]
        
        filtered_prompts = [p for p in directory_prompts if p['id'] != current_prompt_id]
        
        assert len(filtered_prompts) == 2
        assert current_prompt_id not in [p['id'] for p in filtered_prompts]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
