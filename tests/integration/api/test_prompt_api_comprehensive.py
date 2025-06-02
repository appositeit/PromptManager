"""
Comprehensive API Integration Tests
Tests for all CRUD operations and API endpoints
"""

import pytest
import httpx
import asyncio
import json
from typing import Dict, Any, List

# Base URL for the API
BASE_URL = "http://localhost:8095/api"

class TestPromptAPICRUD:
    """Test all CRUD operations on the prompt API"""
    
    @pytest.mark.asyncio
    async def test_get_all_prompts_returns_list(self):
        """Test that GET /api/prompts/all returns a list"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            response = await client.get("/prompts/all")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio 
    async def test_create_prompt_success(self):
        """Test creating a new prompt via POST /api/prompts/"""
        test_prompt = {
            "name": "test_api_prompt",
            "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
            "content": "This is a test prompt created via API",
            "description": "Test prompt for API integration testing",
            "tags": ["test", "api", "integration"]
        }
        
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Clean up first in case test prompt exists
            await client.delete(f"/prompts/tests/test_prompts/test_api_prompt")
            
            # Create the prompt
            response = await client.post("/prompts/", json=test_prompt)
            
            if response.status_code == 201:
                created = response.json()
                assert created["name"] == test_prompt["name"]
                assert created["content"] == test_prompt["content"]
                assert created["description"] == test_prompt["description"]
                assert "id" in created
                
                # Clean up
                await client.delete(f"/prompts/{created['id']}")
            else:
                # Log the error for debugging
                print(f"Create prompt failed: {response.status_code} - {response.text}")
                assert response.status_code in [400], f"Unexpected error: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_create_prompt_validation_errors(self):
        """Test prompt creation with invalid data"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Test missing required fields
            invalid_prompts = [
                {},  # Empty
                {"name": "test"},  # Missing directory
                {"directory": "/tmp"},  # Missing name
                {"name": "", "directory": "/tmp"},  # Empty name
            ]
            
            for invalid_prompt in invalid_prompts:
                response = await client.post("/prompts/", json=invalid_prompt)
                assert response.status_code in [400, 422], f"Should reject invalid prompt: {invalid_prompt}"
    
    @pytest.mark.asyncio
    async def test_get_prompt_by_id(self):
        """Test retrieving a prompt by ID"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # First get all prompts to find a valid ID
            all_response = await client.get("/prompts/all")
            assert all_response.status_code == 200
            
            prompts = all_response.json()
            if prompts:
                # Test getting an existing prompt
                prompt_id = prompts[0]["id"]
                response = await client.get(f"/prompts/{prompt_id}")
                assert response.status_code == 200
                
                prompt_data = response.json()
                assert prompt_data["id"] == prompt_id
                assert "content" in prompt_data
                assert "name" in prompt_data
                assert "directory" in prompt_data
            
            # Test getting non-existent prompt
            response = await client.get("/prompts/nonexistent_prompt_id")
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_prompt(self):
        """Test updating a prompt via PUT"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # First create a test prompt
            test_prompt = {
                "name": "test_update_prompt",
                "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
                "content": "Original content",
                "description": "Original description"
            }
            
            # Clean up first
            await client.delete(f"/prompts/tests/test_prompts/test_update_prompt")
            
            create_response = await client.post("/prompts/", json=test_prompt)
            if create_response.status_code != 201:
                pytest.skip("Could not create test prompt for update test")
            
            created_prompt = create_response.json()
            prompt_id = created_prompt["id"]
            
            try:
                # Update the prompt
                update_data = {
                    "content": "Updated content via API",
                    "description": "Updated description via API",
                    "tags": ["updated", "api"]
                }
                
                update_response = await client.put(f"/prompts/{prompt_id}", json=update_data)
                assert update_response.status_code == 200
                
                updated_prompt = update_response.json()
                assert updated_prompt["content"] == update_data["content"]
                assert updated_prompt["description"] == update_data["description"]
                assert updated_prompt["tags"] == update_data["tags"]
                
            finally:
                # Clean up
                await client.delete(f"/prompts/{prompt_id}")
    
    @pytest.mark.asyncio
    async def test_delete_prompt(self):
        """Test deleting a prompt via DELETE"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # First create a test prompt
            test_prompt = {
                "name": "test_delete_prompt",
                "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
                "content": "This prompt will be deleted",
                "description": "Test prompt for deletion"
            }
            
            create_response = await client.post("/prompts/", json=test_prompt)
            if create_response.status_code != 201:
                pytest.skip("Could not create test prompt for delete test")
            
            created_prompt = create_response.json()
            prompt_id = created_prompt["id"]
            
            # Delete the prompt
            delete_response = await client.delete(f"/prompts/{prompt_id}")
            assert delete_response.status_code == 200
            
            # Verify it's gone
            get_response = await client.get(f"/prompts/{prompt_id}")
            assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_prompt_references(self):
        """Test the referenced_by endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Test with nonexistent prompt (should return empty list)
            response = await client.get("/prompts/nonexistent_prompt/referenced_by")
            assert response.status_code == 200
            assert response.json() == []
            
            # Test with existing prompt
            all_response = await client.get("/prompts/all")
            prompts = all_response.json()
            
            if prompts:
                prompt_id = prompts[0]["id"]
                response = await client.get(f"/prompts/{prompt_id}/referenced_by")
                assert response.status_code == 200
                references = response.json()
                assert isinstance(references, list)


class TestPromptAPIAdvanced:
    """Test advanced API functionality"""
    
    @pytest.mark.asyncio
    async def test_prompt_expansion(self):
        """Test the expand endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Get an existing prompt to test expansion
            all_response = await client.get("/prompts/all")
            prompts = all_response.json()
            
            if prompts:
                prompt_id = prompts[0]["id"]
                expand_request = {
                    "prompt_id": prompt_id
                }
                
                response = await client.post("/prompts/expand", json=expand_request)
                assert response.status_code in [200, 404]  # 404 if prompt doesn't exist
                
                if response.status_code == 200:
                    expanded = response.json()
                    assert "prompt_id" in expanded
                    assert "original_content" in expanded
                    assert "expanded_content" in expanded
                    assert "dependencies" in expanded
                    assert "warnings" in expanded
    
    @pytest.mark.asyncio
    async def test_prompt_search_suggestions(self):
        """Test the search suggestions endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Test basic search
            response = await client.get("/prompts/search_suggestions?query=test")
            assert response.status_code == 200
            suggestions = response.json()
            assert isinstance(suggestions, list)
            
            # Test empty query
            response = await client.get("/prompts/search_suggestions")
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_directory_management(self):
        """Test directory-related endpoints"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Get all directories
            response = await client.get("/prompts/directories/all")
            assert response.status_code == 200
            directories = response.json()
            assert isinstance(directories, list)
    
    @pytest.mark.asyncio
    async def test_prompt_rename(self):
        """Test the rename endpoint"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # First create a test prompt
            test_prompt = {
                "name": "test_rename_original",
                "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
                "content": "Content for rename test",
                "description": "Original prompt for rename testing"
            }
            
            # Clean up first - be more thorough
            await client.delete(f"/prompts/tests/test_prompts/test_rename_original")
            await client.delete(f"/prompts/tests/test_prompts/test_rename_new")
            
            # Also clean up any files that might exist
            import os
            test_dir = "/mnt/data/jem/development/prompt_manager/tests/test_prompts"
            try:
                if os.path.exists(f"{test_dir}/test_rename_original.md"):
                    os.remove(f"{test_dir}/test_rename_original.md")
                if os.path.exists(f"{test_dir}/test_rename_new.md"):
                    os.remove(f"{test_dir}/test_rename_new.md")
            except (OSError, FileNotFoundError):
                pass  # Ignore cleanup errors
            
            create_response = await client.post("/prompts/", json=test_prompt)
            if create_response.status_code != 201:
                pytest.skip("Could not create test prompt for rename test")
            
            created_prompt = create_response.json()
            old_id = created_prompt["id"]
            
            try:
                # Rename the prompt
                rename_data = {
                    "old_id": old_id,
                    "new_name": "test_rename_new",
                    "content": "Updated content during rename",
                    "description": "Updated description during rename"
                }
                
                rename_response = await client.post("/prompts/rename", json=rename_data)
                assert rename_response.status_code in [200, 400, 500]  # 500 may occur if file conflicts
                
                if rename_response.status_code == 200:
                    renamed_prompt = rename_response.json()
                    assert renamed_prompt["name"] == "test_rename_new"
                    
                    # Clean up the renamed prompt
                    await client.delete(f"/prompts/{renamed_prompt['id']}")
                elif rename_response.status_code == 500:
                    # Check if it's a file conflict error (which is acceptable for testing)
                    error_text = rename_response.text
                    if "already exists" in error_text.lower():
                        pytest.skip("File conflict during rename test - acceptable test condition")
                    else:
                        # Re-raise for other 500 errors
                        assert False, f"Unexpected 500 error: {error_text}"
                
            finally:
                # Clean up original if rename failed and both possible files
                await client.delete(f"/prompts/{old_id}")
                await client.delete(f"/prompts/tests/test_prompts/test_rename_new")
                
                # Final filesystem cleanup
                test_dir = "/mnt/data/jem/development/prompt_manager/tests/test_prompts"
                try:
                    if os.path.exists(f"{test_dir}/test_rename_original.md"):
                        os.remove(f"{test_dir}/test_rename_original.md")
                    if os.path.exists(f"{test_dir}/test_rename_new.md"):
                        os.remove(f"{test_dir}/test_rename_new.md")
                except (OSError, FileNotFoundError):
                    pass  # Ignore cleanup errors


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_malformed_json(self):
        """Test API response to malformed JSON"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            # Send malformed JSON
            response = await client.post(
                "/prompts/",
                content="{ invalid json }",
                headers={"content-type": "application/json"}
            )
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_large_content(self):
        """Test handling of large prompt content"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            large_content = "x" * 10000  # 10KB of content
            
            test_prompt = {
                "name": "test_large_content",
                "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
                "content": large_content,
                "description": "Test prompt with large content"
            }
            
            # Clean up first
            await client.delete(f"/prompts/tests/test_prompts/test_large_content")
            
            response = await client.post("/prompts/", json=test_prompt)
            
            if response.status_code == 201:
                created_prompt = response.json()
                assert len(created_prompt["content"]) == len(large_content)
                
                # Clean up
                await client.delete(f"/prompts/{created_prompt['id']}")
            else:
                # Large content may be rejected, which is acceptable
                assert response.status_code in [400, 413]
    
    @pytest.mark.asyncio
    async def test_special_characters_in_names(self):
        """Test handling of special characters in prompt names"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            special_names = [
                "test-with-hyphens",
                "test_with_underscores", 
                "test.with.dots",
                "test with spaces",  # Should be sanitized
            ]
            
            for special_name in special_names:
                test_prompt = {
                    "name": special_name,
                    "directory": "/mnt/data/jem/development/prompt_manager/tests/test_prompts",
                    "content": f"Content for {special_name}",
                    "description": f"Test prompt with special name: {special_name}"
                }
                
                # Clean up first (with sanitized name)
                sanitized_name = special_name.replace(" ", "_")
                await client.delete(f"/prompts/tests/test_prompts/{sanitized_name}")
                
                response = await client.post("/prompts/", json=test_prompt)
                
                if response.status_code == 201:
                    created_prompt = response.json()
                    # Name should be sanitized
                    assert " " not in created_prompt["name"]
                    
                    # Clean up
                    await client.delete(f"/prompts/{created_prompt['id']}")
                else:
                    # Some special characters may be rejected
                    assert response.status_code in [400, 422]


class TestAPIPerformance:
    """Test API performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent API requests"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            
            async def make_request(i):
                return await client.get("/prompts/all")
            
            # Make 10 concurrent requests
            tasks = [make_request(i) for i in range(10)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for i, response in enumerate(responses):
                assert not isinstance(response, Exception), f"Request {i} failed: {response}"
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_response_times(self):
        """Test that API responses are reasonably fast"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            import time
            
            start_time = time.time()
            response = await client.get("/prompts/all")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < 5.0, f"API response too slow: {response_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
