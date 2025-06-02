"""
End-to-End Workflow Tests  
Tests complete user workflows using test prompts
"""

import pytest
from fastapi.testclient import TestClient
import json
from .test_fixtures import TestPromptsHelper

class TestPromptEditingWorkflow:
    """Test the complete prompt editing workflow"""
    
    @pytest.fixture
    def test_prompt_data(self):
        return {
            "name": "workflow_test_prompt",
            "directory": "/tmp/test_workflow",
            "content": "# Test Prompt\n\nThis is initial content.",
            "description": "Test prompt for workflow testing",
            "tags": ["test", "workflow"]
        }
    
    def test_complete_prompt_lifecycle(self, test_client_with_test_prompts, test_prompt_data):
        """Test complete create -> read -> update -> delete workflow"""
        client = test_client_with_test_prompts
        
        # 1. CREATE: Create a new prompt
        create_response = client.post("/api/prompts/", json=test_prompt_data)
        
        if create_response.status_code == 201:
            created_prompt = create_response.json()
            prompt_id = created_prompt["id"]
            
            # 2. READ: Retrieve the created prompt
            read_response = client.get(f"/api/prompts/{prompt_id}")
            assert read_response.status_code == 200
            
            retrieved_prompt = read_response.json()
            assert retrieved_prompt["content"] == test_prompt_data["content"]
            assert retrieved_prompt["description"] == test_prompt_data["description"]
            
            # 3. UPDATE: Modify the prompt
            update_data = {
                "content": "# Updated Test Prompt\n\nThis content has been updated.",
                "description": "Updated description",
                "tags": ["test", "workflow", "updated"]
            }
            
            update_response = client.put(f"/api/prompts/{prompt_id}", json=update_data)
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            
            updated_prompt = update_response.json()
            assert updated_prompt["content"] == update_data["content"]
            assert updated_prompt["description"] == update_data["description"]
            
            # 4. VERIFY UPDATE: Re-read to confirm changes persisted
            verify_response = client.get(f"/api/prompts/{prompt_id}")
            assert verify_response.status_code == 200
            
            verified_prompt = verify_response.json()
            assert verified_prompt["content"] == update_data["content"]
            
            # 5. DELETE: Remove the prompt
            delete_response = client.delete(f"/api/prompts/{prompt_id}")
            assert delete_response.status_code == 200
            
            # 6. VERIFY DELETION: Confirm prompt is gone
            final_read_response = client.get(f"/api/prompts/{prompt_id}")
            assert final_read_response.status_code == 404
    
    def test_prompt_saving_preserves_metadata(self, test_client_with_test_prompts):
        """Test that saving prompts preserves all metadata correctly"""
        client = test_client_with_test_prompts
        
        # Use an existing test prompt for this test
        existing_prompt_response = client.get("/api/prompts/all")
        assert existing_prompt_response.status_code == 200
        
        all_prompts = existing_prompt_response.json()
        
        # Find a specific test prompt
        test_prompt_ids = TestPromptsHelper.get_test_prompt_ids()
        test_prompt = None
        prompt_id = None
        
        for prompt in all_prompts:
            if prompt["id"] in test_prompt_ids:
                test_prompt = prompt
                prompt_id = prompt["id"]
                break
        
        if test_prompt:
            
            # Get full prompt details
            prompt_response = client.get(f"/api/prompts/{prompt_id}")
            assert prompt_response.status_code == 200
            
            original_prompt = prompt_response.json()
            original_created_at = original_prompt.get("created_at")
            original_tags = original_prompt.get("tags", [])
            
            # Update only content, preserve everything else
            update_data = {
                "content": f"{original_prompt.get('content', '')}\n\n<!-- Updated by workflow test -->"
            }
            
            update_response = client.put(f"/api/prompts/{prompt_id}", json=update_data)
            assert update_response.status_code == 200
            
            updated_prompt = update_response.json()
            
            # Verify metadata preservation
            assert updated_prompt.get("created_at") == original_created_at
            assert updated_prompt.get("tags") == original_tags
            assert updated_prompt.get("updated_at") != original_prompt.get("updated_at")
            assert "Updated by workflow test" in updated_prompt.get("content", "")


class TestDependencyTrackingWorkflow:
    """Test prompt dependency and reference tracking workflow"""
    
    def test_referenced_by_tracking(self, test_client_with_test_prompts):
        """Test that referenced_by correctly tracks prompt dependencies"""
        client = test_client_with_test_prompts
        
        # Get all prompts to find ones with dependencies
        all_prompts_response = client.get("/api/prompts/all")
        assert all_prompts_response.status_code == 200
        
        all_prompts = all_prompts_response.json()
        
        # Use known test prompt dependencies
        dependency_relationships = TestPromptsHelper.get_dependency_relationships()
        
        # Find test prompts with dependencies
        prompts_with_deps = []
        reference_targets = set()
        
        for prompt in all_prompts:
            prompt_id = prompt["id"]
            if prompt_id in dependency_relationships:
                dependencies = dependency_relationships[prompt_id]
                prompts_with_deps.append((prompt_id, dependencies))
                reference_targets.update(dependencies)
        
        # Test referenced_by for targets that should have references
        for target in reference_targets:
            # Try different ID formats
            test_ids = [target, f"prompts/{target}"]
            
            for test_id in test_ids:
                ref_response = client.get(f"/api/prompts/{test_id}/referenced_by")
                
                if ref_response.status_code == 200:
                    references = ref_response.json()
                    assert isinstance(references, list), f"referenced_by should return list for {test_id}"
                    
                    # Should have at least one reference
                    assert len(references) > 0, f"Expected references for {test_id} but got none"
                    
                    # Each reference should have required fields
                    for ref in references:
                        assert "id" in ref, f"Reference missing 'id' field: {ref}"
                        assert "directory" in ref, f"Reference missing 'directory' field: {ref}"
                    
                    break  # Found working ID format
            else:
                pytest.fail(f"Could not find working ID format for referenced target: {target}")
    
    def test_dependency_consistency(self, test_client_with_test_prompts):
        """Test that dependency tracking is bidirectionally consistent"""
        client = test_client_with_test_prompts
        
        # Get a prompt with dependencies
        all_prompts_response = client.get("/api/prompts/all")
        assert all_prompts_response.status_code == 200
        
        all_prompts = all_prompts_response.json()
        dependency_relationships = TestPromptsHelper.get_dependency_relationships()
        
        for prompt in all_prompts:
            prompt_id = prompt["id"]
            
            # Only test prompts with known dependencies
            if prompt_id in dependency_relationships:
                expected_deps = dependency_relationships[prompt_id]
                
                # Get full prompt details
                details_response = client.get(f"/api/prompts/{prompt_id}")
                if details_response.status_code == 200:
                    full_prompt = details_response.json()
                    dependencies = full_prompt.get("dependencies", [])
                    
                    if dependencies:
                        # For each dependency, check that this prompt appears in its referenced_by
                        for dep in dependencies:
                            dep_id = dep["id"] if isinstance(dep, dict) else dep
                            
                            # Get referenced_by for the dependency
                            ref_response = client.get(f"/api/prompts/{dep_id}/referenced_by")
                            
                            if ref_response.status_code == 200:
                                references = ref_response.json()
                                referencing_ids = [ref["id"] for ref in references]
                                
                                # This prompt should appear in the dependency's referenced_by list
                                assert prompt_id in referencing_ids, \
                                    f"Bidirectional consistency failed: {prompt_id} depends on {dep_id} " \
                                    f"but {dep_id} doesn't list {prompt_id} in referenced_by"


class TestContentExpansionWorkflow:
    """Test prompt content expansion workflow"""
    
    def test_content_expansion_endpoint(self, test_client_with_test_prompts):
        """Test that content expansion works correctly"""
        client = test_client_with_test_prompts
        
        # Use a known composite test prompt
        composite_prompts = TestPromptsHelper.get_composite_test_prompts()
        
        # Get all prompts to find our test prompts
        all_prompts_response = client.get("/api/prompts/all")
        assert all_prompts_response.status_code == 200
        
        all_prompts = all_prompts_response.json()
        
        # Find a composite test prompt
        test_prompt = None
        for prompt in all_prompts:
            if prompt["id"] in composite_prompts:
                test_prompt = prompt
                break
                
        assert test_prompt is not None, f"Could not find composite test prompt from {composite_prompts}"
        
        prompt_id = test_prompt["id"]
        
        # Get full prompt details
        details_response = client.get(f"/api/prompts/{prompt_id}")
        assert details_response.status_code == 200
        
        full_prompt = details_response.json()
        
        # Test expansion endpoint
        expansion_data = {
            "prompt_id": prompt_id,
            "directory": full_prompt.get("directory")
        }
        
        expand_response = client.post("/api/prompts/expand", json=expansion_data)
        assert expand_response.status_code == 200
        
        expansion = expand_response.json()
        
        # Verify expansion response structure
        required_fields = ["prompt_id", "original_content", "expanded_content", "dependencies"]
        for field in required_fields:
            assert field in expansion, f"Missing field in expansion: {field}"
        
        # Verify content was actually expanded
        original = expansion["original_content"]
        expanded = expansion["expanded_content"]
        
        # Expanded content should be different since we know this is a composite prompt
        assert expanded != original, f"Content should have been expanded for composite prompt {prompt_id}"
        
        # Dependencies should be a list and not empty for composite prompts
        assert isinstance(expansion["dependencies"], list)
        assert len(expansion["dependencies"]) > 0, f"Composite prompt {prompt_id} should have dependencies"
    
    def test_inline_dependency_detection(self, test_client_with_test_prompts):
        """Test that dependencies are correctly detected in prompt content"""
        client = test_client_with_test_prompts
        
        # Get prompts and check their dependency detection
        all_prompts_response = client.get("/api/prompts/all")
        assert all_prompts_response.status_code == 200
        
        all_prompts = all_prompts_response.json()
        dependency_relationships = TestPromptsHelper.get_dependency_relationships()
        
        dependency_checks = []
        
        for prompt in all_prompts:
            prompt_id = prompt["id"]
            
            # Get full prompt details
            details_response = client.get(f"/api/prompts/{prompt_id}")
            if details_response.status_code == 200:
                full_prompt = details_response.json()
                content = full_prompt.get("content", "")
                reported_deps = full_prompt.get("dependencies", [])
                
                # Count embedded references in content
                import re
                embedded_refs = re.findall(r'\[\[([^\]]+)\]\]', content)
                
                # Get expected dependencies for test prompts
                expected_deps = dependency_relationships.get(prompt_id, [])
                
                dependency_checks.append({
                    "prompt_id": prompt_id,
                    "embedded_count": len(embedded_refs),
                    "reported_count": len(reported_deps),
                    "expected_count": len(expected_deps),
                    "embedded_refs": embedded_refs,
                    "reported_deps": [dep["id"] if isinstance(dep, dict) else dep for dep in reported_deps],
                    "expected_deps": expected_deps
                })
        
        # For test prompts with known dependencies, verify accuracy
        for check in dependency_checks:
            if check["prompt_id"] in dependency_relationships:
                # For known test prompts, we can be strict about dependency detection
                expected_count = check["expected_count"]
                reported_count = check["reported_count"]
                
                assert reported_count == expected_count, \
                    f"Dependency count mismatch for {check['prompt_id']}: " \
                    f"expected {expected_count}, reported {reported_count}. " \
                    f"Expected: {check['expected_deps']}, Reported: {check['reported_deps']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
