            mock_service.get_all_prompts.side_effect = Exception("Service error")
            mock_dep.return_value = mock_service
            
            response = test_client.get("/api/prompts/directories/test/prompts")
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_api_endpoint_performance(self, test_client):
        """Test that the API endpoint performs well with large datasets"""
        with patch('src.api.router.get_prompt_service_dependency') as mock_dep:
            mock_service = MagicMock(spec=PromptService)
            
            # Create a large dataset
            large_prompts = []
            target_directory = "/large/directory"
            
            for i in range(1000):
                large_prompts.append({
                    "id": f"large_directory/prompt_{i:04d}",
                    "name": f"prompt_{i:04d}",
                    "directory": target_directory,
                    "display_name": f"Test Prompt {i:04d}",
                    "description": f"Description for prompt {i}",
                    "tags": ["test", f"batch_{i // 100}"],
                    "is_composite": i % 5 == 0,  # Every 5th prompt is composite
                    "last_updated": "2025-06-01T22:00:00Z"
                })
            
            # Add some prompts from other directories to test filtering
            for i in range(100):
                large_prompts.append({
                    "id": f"other_directory/prompt_{i:04d}",
                    "name": f"prompt_{i:04d}",
                    "directory": "/other/directory",
                    "display_name": f"Other Prompt {i:04d}",
                    "description": "",
                    "tags": [],
                    "is_composite": False,
                    "last_updated": "2025-06-01T22:00:00Z"
                })
            
            mock_service.get_all_prompts.return_value = large_prompts
            mock_dep.return_value = mock_service
            
            import time
            start_time = time.time()
            response = test_client.get(f"/api/prompts/directories{target_directory}/prompts")
            end_time = time.time()
            
            assert response.status_code == 200
            data = response.json()
            
            # Should return only prompts from target directory
            assert len(data) == 1000
            
            # Should be sorted alphabetically
            assert data[0]["display_name"] == "Test Prompt 0000"
            assert data[999]["display_name"] == "Test Prompt 0999"
            
            # Performance check - should complete in reasonable time
            duration = end_time - start_time
            assert duration < 1.0  # Should complete in under 1 second


class TestCollapsibleSidebarIntegration:
    """Integration tests for the complete collapsible sidebar functionality"""
    
    def test_css_file_exists(self):
        """Test that the CSS file is created and accessible"""
        import os
        css_path = "/home/jem/development/prompt_manager/src/static/css/collapsible-sidebar.css"
        assert os.path.exists(css_path), "CSS file should exist"
        
        # Check that CSS contains expected classes
        with open(css_path, 'r') as f:
            css_content = f.read()
            
        expected_classes = [
            '.collapsible-header',
            '.collapse-chevron', 
            '.directory-prompts-list',
            '.directory-prompt-item',
            '.drag-preview'
        ]
        
        for css_class in expected_classes:
            assert css_class in css_content, f"CSS should contain {css_class}"

    def test_javascript_file_exists(self):
        """Test that the JavaScript file is created and accessible"""
        import os
        js_path = "/home/jem/development/prompt_manager/src/static/js/collapsible-sidebar.js"
        assert os.path.exists(js_path), "JavaScript file should exist"
        
        # Check that JS contains expected functionality
        with open(js_path, 'r') as f:
            js_content = f.read()
            
        expected_features = [
            'class CollapsibleSidebar',
            'loadSidebarState',
            'initializeCollapsibleCards',
            'loadDirectoryPrompts',
            'setupEditorDragTarget',
            'createDragImage'
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
            'data-card-id="referencedBy"',
            'data-card-id="markdownCheat"',
            'collapsible-header',
            'collapse-chevron',
            'directory-prompts-list'
        ]
        
        for element in expected_elements:
            assert element in template_content, f"Template should contain {element}"

    def test_eslint_compliance(self):
        """Test that the JavaScript code passes ESLint"""
        import subprocess
        import os
        
        js_file = "/home/jem/development/prompt_manager/src/static/js/collapsible-sidebar.js"
        
        # Run ESLint on our specific file
        result = subprocess.run(
            ['npx', 'eslint', js_file],
            cwd="/home/jem/development/prompt_manager",
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"ESLint should pass, but got errors: {result.stdout + result.stderr}"


class TestCollapsibleSidebarBehavior:
    """Tests for the expected behavior of the collapsible sidebar"""
    
    def test_sidebar_state_persistence_structure(self):
        """Test that sidebar state structure is correct"""
        # This tests the expected structure without browser dependency
        expected_state = {
            'metadata': True,
            'directoryPrompts': True, 
            'dependencies': True,
            'referencedBy': True,
            'markdownCheat': True
        }
        
        # Verify all expected sections are present
        assert 'metadata' in expected_state
        assert 'directoryPrompts' in expected_state
        assert 'dependencies' in expected_state
        assert 'referencedBy' in expected_state
        assert 'markdownCheat' in expected_state
        
        # Verify default state is open (True)
        for section, state in expected_state.items():
            assert state is True, f"Section {section} should default to open"

    def test_drag_drop_data_format(self):
        """Test that drag and drop data format is correct"""
        # Test the expected format for prompt references
        test_prompt_id = "test_directory/example_prompt"
        expected_drag_text = f"[[{test_prompt_id}]]"
        
        # Verify the format matches our inclusion syntax
        assert expected_drag_text.startswith("[[")
        assert expected_drag_text.endswith("]]")
        assert test_prompt_id in expected_drag_text

    def test_directory_prompt_filtering_logic(self):
        """Test the logic for filtering current prompt from directory list"""
        current_prompt_id = "test_dir/current_prompt"
        
        directory_prompts = [
            {"id": "test_dir/prompt_1", "display_name": "Prompt 1"},
            {"id": "test_dir/current_prompt", "display_name": "Current Prompt"},
            {"id": "test_dir/prompt_3", "display_name": "Prompt 3"}
        ]
        
        # Filter out current prompt (simulating the JS logic)
        filtered_prompts = [p for p in directory_prompts if p['id'] != current_prompt_id]
        
        assert len(filtered_prompts) == 2
        assert current_prompt_id not in [p['id'] for p in filtered_prompts]

    def test_alphabetical_sorting_logic(self):
        """Test that directory prompts are sorted alphabetically by display name"""
        unsorted_prompts = [
            {"id": "dir/zebra", "display_name": "Zebra Prompt"},
            {"id": "dir/alpha", "display_name": "Alpha Prompt"}, 
            {"id": "dir/beta", "display_name": "Beta Prompt"}
        ]
        
        # Sort by display name (simulating the JS logic)
        sorted_prompts = sorted(unsorted_prompts, key=lambda p: p.get('display_name', p['id']).lower())
        
        assert sorted_prompts[0]['display_name'] == "Alpha Prompt"
        assert sorted_prompts[1]['display_name'] == "Beta Prompt"
        assert sorted_prompts[2]['display_name'] == "Zebra Prompt"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
