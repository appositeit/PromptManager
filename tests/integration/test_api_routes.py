"""
API Route Integration Tests
Tests for actual HTTP routes and their behavior
"""

import pytest
import requests
from fastapi.testclient import TestClient
from src.server import app

class TestPromptAPIRoutes:
    """Test all prompt-related API routes work correctly"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_all_routes_registered(self, client):
        """Test that all expected routes are registered and accessible"""
        # Test route discovery via OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec["paths"]
        
        # Verify all critical routes exist
        expected_routes = [
            "/api/prompts/",  # POST create
            "/api/prompts/{prompt_id}",  # GET, PUT, DELETE
            "/api/prompts/{prompt_id}/referenced_by",  # GET references
            "/api/prompts/all",  # GET all prompts
            "/api/prompts/expand",  # POST expand content
        ]
        
        for route in expected_routes:
            assert any(route in path for path in paths), f"Route {route} not found in API spec"
    
    def test_route_methods_correct(self, client):
        """Test that each route supports the correct HTTP methods"""
        test_prompt_id = "test_prompt_for_method_testing"
        
        # Test that GET works (should return 200 or 404, not 405)
        get_response = client.get(f"/api/prompts/{test_prompt_id}")
        assert get_response.status_code in [200, 404], f"GET should work, got {get_response.status_code}"
        assert get_response.status_code != 405, "GET method should be allowed"
        
        # Test that PUT works (should return 200, 404, or 400, not 405)
        put_response = client.put(f"/api/prompts/{test_prompt_id}", json={"content": "test"})
        assert put_response.status_code in [200, 404, 400], f"PUT should work, got {put_response.status_code}"
        assert put_response.status_code != 405, "PUT method should be allowed"
        
        # Test that DELETE works (should return 200 or 404, not 405)
        delete_response = client.delete(f"/api/prompts/{test_prompt_id}")
        assert delete_response.status_code in [200, 404], f"DELETE should work, got {delete_response.status_code}"
        assert delete_response.status_code != 405, "DELETE method should be allowed"
        
        # Ensure POST is NOT allowed on specific prompt routes (should be 405)
        post_response = client.post(f"/api/prompts/{test_prompt_id}", json={"content": "test"})
        assert post_response.status_code == 405, "POST should not be allowed on specific prompt routes"
    
    def test_route_ordering_priority(self, client):
        """Test that specific routes take precedence over catch-all routes"""
        
        # 1. Test that referenced_by route works (not caught by catch-all)
        response = client.get("/api/prompts/prompts/test_prompt/referenced_by")
        # Should get 200 or 404 (prompt not found), NOT HTML error page
        assert response.status_code in [200, 404]
        assert response.headers.get("content-type", "").startswith("application/json")
        
        # 2. Test that PUT route works (not caught by catch-all GET)
        response = client.put("/api/prompts/prompts/test_prompt", json={"content": "test"})
        # Should get 200 or 404 (prompt not found), NOT 405 Method Not Allowed
        assert response.status_code in [200, 404], f"PUT failed with {response.status_code}: {response.text}"
        assert response.status_code != 405, "PUT route being caught by GET-only catch-all route"
    
    def test_complex_prompt_ids_with_slashes(self, client):
        """Test that prompt IDs containing slashes work correctly"""
        complex_id = "prompts/test_prompt"
        
        # Test GET
        response = client.get(f"/api/prompts/{complex_id}")
        assert response.status_code in [200, 404]  # Valid response, not 500 or HTML
        
        # Test PUT  
        response = client.put(f"/api/prompts/{complex_id}", json={"content": "test"})
        assert response.status_code in [200, 404, 400]  # Valid response, not 405
        
        # Test referenced_by
        response = client.get(f"/api/prompts/{complex_id}/referenced_by")
        assert response.status_code in [200, 404]  # Valid response, not HTML error


class TestRouteRegression:
    """Tests to catch route registration regressions"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_no_route_conflicts(self, client):
        """Detect if routes are conflicting with each other"""
        
        # Create a comprehensive test matrix
        test_cases = [
            # (method, path, expected_status_range)
            ("GET", "/api/prompts/all", [200]),
            ("GET", "/api/prompts/test/referenced_by", [200, 404]),
            ("PUT", "/api/prompts/test", [200, 400, 404]),
            ("DELETE", "/api/prompts/test", [200, 404]),
            ("POST", "/api/prompts/", [201, 400]),
        ]
        
        for method, path, expected_statuses in test_cases:
            if method == "GET":
                response = client.get(path)
            elif method == "PUT":
                response = client.put(path, json={"content": "test"})
            elif method == "DELETE":
                response = client.delete(path)
            elif method == "POST":
                response = client.post(path, json={"name": "test", "directory": "/test"})
            
            assert response.status_code in expected_statuses, \
                f"{method} {path} returned {response.status_code}, expected one of {expected_statuses}"
            
            # Ensure we're not getting HTML error pages for API routes
            content_type = response.headers.get("content-type", "")
            assert not content_type.startswith("text/html"), \
                f"{method} {path} returned HTML instead of JSON: {response.text[:100]}"
    
    def test_route_order_invariant(self, client):
        """Test that route order doesn't affect functionality"""
        
        # This test would ideally run multiple times with different route orders
        # For now, test that specific routes aren't being overridden
        
        test_prompt_id = "prompts/route_test"
        
        # Test sequence that should work regardless of route order
        responses = []
        
        # 1. Try to get non-existent prompt (should be 404, not HTML)
        responses.append(("GET", client.get(f"/api/prompts/{test_prompt_id}")))
        
        # 2. Try to get references for non-existent prompt  
        responses.append(("GET_REF", client.get(f"/api/prompts/{test_prompt_id}/referenced_by")))
        
        # 3. Try to update non-existent prompt
        responses.append(("PUT", client.put(f"/api/prompts/{test_prompt_id}", json={"content": "test"})))
        
        # Verify all responses are proper API responses, not route conflicts
        for operation, response in responses:
            assert response.headers.get("content-type", "").startswith("application/json"), \
                f"{operation} returned non-JSON response: {response.headers.get('content-type')}"
            
            # Should be proper 404s, not route conflicts
            if response.status_code == 404:
                error_detail = response.json().get("detail", "")
                assert "not found" in error_detail.lower(), \
                    f"{operation} gave unexpected 404 message: {error_detail}"


class TestAPIEndpointFunctionality:
    """Test actual functionality of each endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_prompt_data(self):
        return {
            "name": "test_route_prompt",
            "directory": "/tmp/test",
            "content": "This is test content",
            "description": "Test prompt for route testing"
        }
    
    def test_create_prompt_endpoint(self, client, sample_prompt_data):
        """Test POST /api/prompts/ creates prompts correctly"""
        response = client.post("/api/prompts/", json=sample_prompt_data)
        
        # Should create successfully or fail with validation error
        assert response.status_code in [201, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 201:
            created_prompt = response.json()
            assert created_prompt["name"] == sample_prompt_data["name"]
            assert created_prompt["content"] == sample_prompt_data["content"]
    
    def test_update_prompt_endpoint(self, client):
        """Test PUT /api/prompts/{id} updates prompts correctly"""
        
        update_data = {
            "content": "Updated content for route test",
            "description": "Updated description"
        }
        
        # Test with a known prompt ID format
        response = client.put("/api/prompts/prompts/test_prompt", json=update_data)
        
        # Should succeed, return 404 for missing prompt, or 400 for validation
        assert response.status_code in [200, 404, 400]
        assert response.status_code != 405, "PUT route not working - method not allowed"
        
        if response.status_code == 200:
            updated_prompt = response.json()
            assert updated_prompt["content"] == update_data["content"]
    
    def test_referenced_by_endpoint(self, client):
        """Test GET /api/prompts/{id}/referenced_by returns references"""
        
        response = client.get("/api/prompts/prompts/test_prompt/referenced_by")
        
        # Should return references list or 404 for missing prompt
        assert response.status_code in [200, 404]
        assert response.status_code != 405, "referenced_by route not working"
        
        if response.status_code == 200:
            references = response.json()
            assert isinstance(references, list), "referenced_by should return a list"
    
    def test_expand_content_endpoint(self, client):
        """Test POST /api/prompts/expand expands prompt content"""
        
        expand_data = {
            "prompt_id": "test_prompt",
            "directory": "/tmp/test"
        }
        
        response = client.post("/api/prompts/expand", json=expand_data)
        
        # Should expand or return 404 for missing prompt
        assert response.status_code in [200, 404, 400]
        
        if response.status_code == 200:
            expanded = response.json()
            required_fields = ["prompt_id", "original_content", "expanded_content", "dependencies"]
            for field in required_fields:
                assert field in expanded, f"Missing field in expansion response: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
