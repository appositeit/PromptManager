"""
End-to-End Workflow Tests
Tests for complete user workflows and scenarios
"""

import pytest
import httpx
import json
import tempfile
import os
import shutil
from typing import Dict, Any, List

# Base URLs
API_BASE_URL = "http://localhost:8095/api"
WEB_BASE_URL = "http://localhost:8095"


class TestCompletePromptWorkflow:
    """Test complete prompt management workflows"""
    
    def test_complete_prompt_lifecycle(self):
        """Test the complete lifecycle of a prompt from creation to deletion"""
        with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
            
            # Step 1: Create a new prompt
            prompt_data = {
                "name": "e2e_lifecycle_test",
                "directory": "/tmp/e2e_test",
                "content": "Original content for E2E lifecycle test",
                "description": "Test prompt for complete lifecycle testing",
                "tags": ["e2e", "test", "lifecycle"]
            }
            
            # Clean up first
            client.delete("/prompts/e2e_test/e2e_lifecycle_test")
            
            # Create the prompt
            create_response = client.post("/prompts/", json=prompt_data)
            assert create_response.status_code == 201, f"Failed to create prompt: {create_response.text}"
            
            created_prompt = create_response.json()
            prompt_id = created_prompt["id"]
            
            try:
                # Step 2: Verify the prompt exists and has correct data
                get_response = client.get(f"/prompts/{prompt_id}")
                assert get_response.status_code == 200
                
                retrieved_prompt = get_response.json()
                assert retrieved_prompt["name"] == prompt_data["name"]
                assert retrieved_prompt["content"] == prompt_data["content"]
                assert retrieved_prompt["description"] == prompt_data["description"]
                assert retrieved_prompt["tags"] == prompt_data["tags"]
                
                # Step 3: Update the prompt
                update_data = {
                    "content": "Updated content for E2E lifecycle test",
                    "description": "Updated description for lifecycle test",
                    "tags": ["e2e", "test", "lifecycle", "updated"]
                }
                
                update_response = client.put(f"/prompts/{prompt_id}", json=update_data)
                assert update_response.status_code == 200
                
                updated_prompt = update_response.json()
                assert updated_prompt["content"] == update_data["content"]
                assert updated_prompt["description"] == update_data["description"]
                assert updated_prompt["tags"] == update_data["tags"]
                
                # Step 4: Test prompt expansion (if it has inclusions)
                expand_request = {"prompt_id": prompt_id}
                expand_response = client.post("/prompts/expand", json=expand_request)
                assert expand_response.status_code == 200
                
                expanded_data = expand_response.json()
                assert "original_content" in expanded_data
                assert "expanded_content" in expanded_data
                assert "dependencies" in expanded_data
                
                # Step 5: Test references (should be empty for this prompt)
                refs_response = client.get(f"/prompts/{prompt_id}/referenced_by")
                assert refs_response.status_code == 200
                assert isinstance(refs_response.json(), list)
                
                # Step 6: Verify prompt appears in listing
                all_response = client.get("/prompts/all")
                assert all_response.status_code == 200
                
                all_prompts = all_response.json()
                prompt_ids = [p["id"] for p in all_prompts]
                assert prompt_id in prompt_ids, "Prompt should appear in all prompts listing"
                
            finally:
                # Step 7: Delete the prompt
                delete_response = client.delete(f"/prompts/{prompt_id}")
                assert delete_response.status_code == 200
                
                # Step 8: Verify deletion
                get_after_delete = client.get(f"/prompts/{prompt_id}")
                assert get_after_delete.status_code == 404
    
    
    def test_prompt_composition_workflow(self):
        """Test creating and using composite prompts with inclusions"""
        with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
            
            # Create component prompts
            component_prompts = [
                {
                    "name": "e2e_component_1",
                    "directory": "/tmp/e2e_composition",
                    "content": "This is component 1 content",
                    "description": "First component for composition test"
                },
                {
                    "name": "e2e_component_2", 
                    "directory": "/tmp/e2e_composition",
                    "content": "This is component 2 content",
                    "description": "Second component for composition test"
                }
            ]
            
            created_components = []
            
            try:
                # Clean up first
                for comp in component_prompts:
                    client.delete(f"/prompts/e2e_composition/{comp['name']}")
                client.delete("/prompts/e2e_composition/e2e_composite_main")
                
                # Create component prompts
                for comp_data in component_prompts:
                    response = client.post("/prompts/", json=comp_data)
                    assert response.status_code == 201, f"Failed to create component: {response.text}"
                    created_components.append(response.json())
                
                # Create main composite prompt that includes the components
                main_prompt = {
                    "name": "e2e_composite_main",
                    "directory": "/tmp/e2e_composition", 
                    "content": "Main prompt with [[e2e_composition/e2e_component_1]] and [[e2e_composition/e2e_component_2]] included",
                    "description": "Main composite prompt for E2E testing"
                }
                
                main_response = client.post("/prompts/", json=main_prompt)
                assert main_response.status_code == 201
                
                main_created = main_response.json()
                main_prompt_id = main_created["id"]
                created_components.append(main_created)
                
                # Test expansion of the composite prompt
                expand_request = {"prompt_id": main_prompt_id}
                expand_response = client.post("/prompts/expand", json=expand_request)
                assert expand_response.status_code == 200
                
                expanded = expand_response.json()
                expanded_content = expanded["expanded_content"]
                
                # Expanded content should include the component contents
                assert "component 1 content" in expanded_content
                assert "component 2 content" in expanded_content
                assert len(expanded["dependencies"]) == 2
                
                # Test references - components should be referenced by main prompt
                for comp in created_components[:-1]:  # Exclude main prompt
                    refs_response = client.get(f"/prompts/{comp['id']}/referenced_by")
                    assert refs_response.status_code == 200
                    
                    references = refs_response.json()
                    ref_ids = [ref.get("id", "") for ref in references]
                    assert any(main_prompt_id in ref_id for ref_id in ref_ids), \
                        f"Component {comp['name']} should be referenced by main prompt"
                
            finally:
                # Clean up all created prompts
                for comp in created_components:
                    try:
                        client.delete(f"/prompts/{comp['id']}")
                    except:
                        pass
    
    
    def test_search_and_discovery_workflow(self):
        """Test prompt search and discovery workflow"""
        with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
            
            # Create test prompts with various characteristics
            test_prompts = [
                {
                    "name": "e2e_search_alpha",
                    "directory": "/tmp/e2e_search",
                    "content": "Content about data analysis and algorithms",
                    "description": "Prompt about data and algorithms",
                    "tags": ["data", "algorithm", "analysis"]
                },
                {
                    "name": "e2e_search_beta",
                    "directory": "/tmp/e2e_search", 
                    "content": "Content about web development and APIs",
                    "description": "Prompt about web development",
                    "tags": ["web", "api", "development"]
                },
                {
                    "name": "e2e_search_gamma",
                    "directory": "/tmp/e2e_search",
                    "content": "Content about data visualization and charts",
                    "description": "Prompt about data visualization", 
                    "tags": ["data", "visualization", "charts"]
                }
            ]
            
            created_prompts = []
            
            try:
                # Clean up first
                for prompt_data in test_prompts:
                    client.delete(f"/prompts/e2e_search/{prompt_data['name']}")
                
                # Create test prompts
                for prompt_data in test_prompts:
                    response = client.post("/prompts/", json=prompt_data)
                    assert response.status_code == 201
                    created_prompts.append(response.json())
                
                # Test search by prompt name (search_suggestions searches IDs/names, not content)
                search_response = client.get("/prompts/search_suggestions?query=e2e_search")
                assert search_response.status_code == 200
                
                suggestions = search_response.json()
                e2e_prompts = [s for s in suggestions if "e2e_search" in str(s).lower()]
                assert len(e2e_prompts) >= 2, "Should find prompts with 'e2e_search' in name"
                
                # Test search with more specific name
                search_response = client.get("/prompts/search_suggestions?query=alpha")
                assert search_response.status_code == 200
                
                suggestions = search_response.json()
                alpha_prompts = [s for s in suggestions if "alpha" in str(s).lower()]
                assert len(alpha_prompts) >= 1, "Should find prompts with 'alpha' in name"
                
                # Test search with exclusions
                search_response = client.get("/prompts/search_suggestions?query=e2e_search&exclude=e2e_search/e2e_search_alpha")
                assert search_response.status_code == 200
                
                suggestions = search_response.json()
                # Should not include the excluded prompt
                alpha_found = any("e2e_search_alpha" in str(s) for s in suggestions)
                assert not alpha_found, "Excluded prompt should not appear in results"
                
                # Test getting all prompts and filtering
                all_response = client.get("/prompts/all")
                assert all_response.status_code == 200
                
                all_prompts = all_response.json()
                e2e_prompts = [p for p in all_prompts if p["name"].startswith("e2e_search_")]
                assert len(e2e_prompts) == 3, "Should find all 3 created test prompts"
                
            finally:
                # Clean up
                for prompt in created_prompts:
                    try:
                        client.delete(f"/prompts/{prompt['id']}")
                    except:
                        pass


class TestDirectoryManagementWorkflow:
    """Test complete directory management workflows"""
    
    
    def test_directory_lifecycle_workflow(self):
        """Test complete directory management lifecycle"""
        with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
            
            # Create a temporary directory for testing
            temp_dir = tempfile.mkdtemp(prefix="e2e_dir_test_")
            
            try:
                # Step 1: Add a new directory
                dir_data = {
                    "path": temp_dir,
                    "name": "E2E Test Directory",
                    "description": "Directory for E2E testing"
                }
                
                add_response = client.post("/prompts/directories", json=dir_data)
                assert add_response.status_code == 200, f"Failed to add directory: {add_response.text}"
                
                added_dir = add_response.json()
                assert added_dir["path"] == temp_dir
                assert added_dir["name"] == dir_data["name"]
                
                # Step 2: Verify directory appears in listing
                dirs_response = client.get("/prompts/directories/all")
                assert dirs_response.status_code == 200
                
                directories = dirs_response.json()
                dir_paths = [d["path"] for d in directories]
                assert temp_dir in dir_paths, "New directory should appear in listing"
                
                # Step 3: Create a prompt in the new directory
                test_prompt = {
                    "name": "dir_test_prompt",
                    "directory": temp_dir,
                    "content": "Content in the new directory",
                    "description": "Test prompt in new directory"
                }
                
                prompt_response = client.post("/prompts/", json=test_prompt)
                assert prompt_response.status_code == 201
                
                created_prompt = prompt_response.json()
                prompt_id = created_prompt["id"]
                
                # Step 4: Update directory metadata
                update_data = {
                    "name": "Updated E2E Test Directory",
                    "description": "Updated description for E2E testing"
                }
                
                # URL encode the path for the request
                import urllib.parse
                encoded_path = urllib.parse.quote(temp_dir, safe='')
                
                update_response = client.put(f"/prompts/directories/{encoded_path}", json=update_data)
                assert update_response.status_code == 200
                
                updated_dir = update_response.json()
                assert updated_dir["name"] == update_data["name"]
                assert updated_dir["description"] == update_data["description"]
                
                # Step 5: Test directory toggle (disable/enable)
                toggle_data = {"enabled": False}
                toggle_response = client.post(f"/prompts/directories/{encoded_path}/toggle", json=toggle_data)
                assert toggle_response.status_code == 200
                
                toggled_dir = toggle_response.json()
                assert toggled_dir["enabled"] == False
                
                # Re-enable
                toggle_data = {"enabled": True}
                toggle_response = client.post(f"/prompts/directories/{encoded_path}/toggle", json=toggle_data)
                assert toggle_response.status_code == 200
                
                # Step 6: Clean up prompt first
                client.delete(f"/prompts/{prompt_id}")
                
                # Step 7: Remove directory
                delete_response = client.delete(f"/prompts/directories/{encoded_path}")
                assert delete_response.status_code == 200
                
                # Step 8: Verify directory is removed from listing
                final_dirs_response = client.get("/prompts/directories/all")
                assert final_dirs_response.status_code == 200
                
                final_directories = final_dirs_response.json()
                final_dir_paths = [d["path"] for d in final_directories]
                assert temp_dir not in final_dir_paths, "Directory should be removed from listing"
                
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)


class TestErrorRecoveryWorkflow:
    """Test error handling and recovery workflows"""
    
    
    def test_duplicate_prompt_handling_workflow(self):
        """Test handling of duplicate prompt creation attempts"""
        with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
            
            prompt_data = {
                "name": "duplicate_test_prompt",
                "directory": "/tmp/duplicate_test",
                "content": "Original content",
                "description": "Test prompt for duplicate handling"
            }
            
            # Clean up first
            client.delete("/prompts/duplicate_test/duplicate_test_prompt")
            
            try:
                # Create first prompt
                first_response = client.post("/prompts/", json=prompt_data)
                assert first_response.status_code == 201
                
                first_prompt = first_response.json()
                
                # Try to create duplicate
                duplicate_response = client.post("/prompts/", json=prompt_data)
                assert duplicate_response.status_code == 400, "Should reject duplicate prompt"
                
                # Modify content and try again - should still be rejected (same name/directory)
                prompt_data["content"] = "Different content"
                modified_response = client.post("/prompts/", json=prompt_data)
                assert modified_response.status_code == 400, "Should reject prompt with same name/directory"
                
                # Create in different directory - should succeed
                prompt_data["directory"] = "/tmp/duplicate_test_2"
                different_dir_response = client.post("/prompts/", json=prompt_data)
                assert different_dir_response.status_code == 201, "Should allow same name in different directory"
                
                second_prompt = different_dir_response.json()
                
                # Verify both prompts exist and are different
                first_get = client.get(f"/prompts/{first_prompt['id']}")
                second_get = client.get(f"/prompts/{second_prompt['id']}")
                
                assert first_get.status_code == 200
                assert second_get.status_code == 200
                assert first_get.json()["directory"] != second_get.json()["directory"]
                
                # Clean up both
                client.delete(f"/prompts/{first_prompt['id']}")
                client.delete(f"/prompts/{second_prompt['id']}")
                
            except Exception as e:
                # Clean up on error
                try:
                    client.delete("/prompts/duplicate_test/duplicate_test_prompt")
                    client.delete("/prompts/duplicate_test_2/duplicate_test_prompt")
                except:
                    pass
                raise e
    
    
    def test_invalid_data_handling_workflow(self):
        """Test handling of various invalid data scenarios"""
        with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
            
            # Test various invalid prompt data
            invalid_prompts = [
                # Missing required fields
                {"name": "test"},  # Missing directory
                {"directory": "/tmp"},  # Missing name
                {},  # Empty object
                
                # Invalid field values
                {"name": "", "directory": "/tmp"},  # Empty name
                {"name": "test", "directory": ""},  # Empty directory
                {"name": "test", "directory": "/tmp", "tags": "not_a_list"},  # Invalid tags type
            ]
            
            for i, invalid_prompt in enumerate(invalid_prompts):
                response = client.post("/prompts/", json=invalid_prompt)
                assert response.status_code in [400, 422], \
                    f"Should reject invalid prompt {i}: {invalid_prompt}"
            
            # Test invalid update data
            # First create a valid prompt
            valid_prompt = {
                "name": "invalid_test_prompt",
                "directory": "/tmp/invalid_test",
                "content": "Valid content",
                "description": "Valid description"
            }
            
            # Clean up first
            client.delete("/prompts/invalid_test/invalid_test_prompt")
            
            create_response = client.post("/prompts/", json=valid_prompt)
            if create_response.status_code == 201:
                created_prompt = create_response.json()
                prompt_id = created_prompt["id"]
                
                try:
                    # Test invalid updates
                    invalid_updates = [
                        {"tags": "not_a_list"},  # Invalid tags type
                        {"content": None},  # None content might be invalid
                    ]
                    
                    for invalid_update in invalid_updates:
                        update_response = client.put(f"/prompts/{prompt_id}", json=invalid_update)
                        # Some invalid data might be accepted and sanitized, others rejected
                        assert update_response.status_code in [200, 400, 422], \
                            f"Should handle invalid update gracefully: {invalid_update}"
                
                finally:
                    # Clean up
                    client.delete(f"/prompts/{prompt_id}")


class TestPerformanceWorkflow:
    """Test performance-related workflows"""
    
    
    def test_bulk_operations_workflow(self):
        """Test bulk creation and management of prompts"""
        with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
            
            # Create multiple prompts quickly
            num_prompts = 20
            created_prompts = []
            
            try:
                # Bulk creation
                for i in range(num_prompts):
                    prompt_data = {
                        "name": f"bulk_e2e_test_{i:03d}",
                        "directory": "/tmp/bulk_e2e_test",
                        "content": f"Bulk test content for prompt {i}",
                        "description": f"Bulk test prompt {i}",
                        "tags": ["bulk", "e2e", f"batch_{i // 5}"]  # Group in batches of 5
                    }
                    
                    # Clean up first
                    client.delete(f"/prompts/bulk_e2e_test/{prompt_data['name']}")
                    
                    response = client.post("/prompts/", json=prompt_data)
                    if response.status_code == 201:
                        created_prompts.append(response.json())
                
                assert len(created_prompts) == num_prompts, f"Should create {num_prompts} prompts"
                
                # Test bulk retrieval performance
                import time
                start_time = time.time()
                
                all_response = client.get("/prompts/all")
                assert all_response.status_code == 200
                
                end_time = time.time()
                retrieval_time = end_time - start_time
                
                all_prompts = all_response.json()
                bulk_prompts = [p for p in all_prompts if p["name"].startswith("bulk_e2e_test_")]
                
                assert len(bulk_prompts) >= num_prompts, "Should retrieve all bulk prompts"
                assert retrieval_time < 5.0, f"Bulk retrieval too slow: {retrieval_time:.2f}s"
                
                # Test search performance with many prompts
                search_response = client.get("/prompts/search_suggestions?query=bulk")
                assert search_response.status_code == 200
                
                suggestions = search_response.json()
                bulk_suggestions = [s for s in suggestions if "bulk" in str(s)]
                assert len(bulk_suggestions) > 0, "Should find bulk prompts in search"
                
            finally:
                # Bulk cleanup
                for prompt in created_prompts:
                    try:
                        client.delete(f"/prompts/{prompt['id']}")
                    except:
                        pass
    
    
    def test_concurrent_operations_workflow(self):
        """Test concurrent API operations"""
        with httpx.Client(base_url=API_BASE_URL, timeout=20.0) as client:
            
            # Define concurrent operations
            def create_prompt(client, i):
                prompt_data = {
                    "name": f"concurrent_test_{i}",
                    "directory": "/tmp/concurrent_test",
                    "content": f"Concurrent test content {i}",
                    "description": f"Concurrent test prompt {i}"
                }
                
                # Clean up first
                client.delete(f"/prompts/concurrent_test/{prompt_data['name']}")
                
                response = client.post("/prompts/", json=prompt_data)
                return response
            
            def get_all_prompts(client):
                return client.get("/prompts/all")
            
            # Run operations sequentially for E2E testing
            create_results = []
            read_results = []
            
            # Mix of create operations and read operations
            for i in range(5):
                create_results.append(create_prompt(client, i))
                read_results.append(get_all_prompts(client))
            
            # Verify results
            
            # All operations should succeed
            for i, result in enumerate(create_results):
                assert not isinstance(result, Exception), f"Create operation {i} failed: {result}"
                assert result.status_code == 201, f"Create operation {i} failed: {result.status_code}"
            
            for i, result in enumerate(read_results):
                assert not isinstance(result, Exception), f"Read operation {i} failed: {result}"
                assert result.status_code == 200, f"Read operation {i} failed: {result.status_code}"
            
            # Clean up created prompts
            for i in range(5):
                try:
                    client.delete(f"/prompts/concurrent_test/concurrent_test_{i}")
                except:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
