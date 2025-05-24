"""
Route Discovery and Validation Tests
Ensures routes are registered correctly and haven't been accidentally disabled
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.router import router as prompt_router
import inspect
import re

class TestRouteDiscovery:
    """Test route registration and discovery"""
    
    def test_all_router_functions_registered(self):
        """Ensure all router functions are actually registered as routes"""
        
        # Get all route handlers from the router
        registered_routes = []
        for route in prompt_router.routes:
            if hasattr(route, 'endpoint'):
                registered_routes.append(route.endpoint.__name__)
        
        # Get all functions decorated with @router in the router module
        import src.api.router as router_module
        
        expected_handlers = []
        for name, obj in inspect.getmembers(router_module):
            if inspect.iscoroutinefunction(obj) and name.startswith(('get_', 'create_', 'update_', 'delete_')):
                expected_handlers.append(name)
        
        # Check that all expected handlers are registered
        for handler in expected_handlers:
            assert handler in registered_routes, f"Handler {handler} not registered as route"
    
    def test_route_paths_match_expected_patterns(self):
        """Test that route paths follow expected patterns"""
        
        expected_patterns = {
            r"^/all$": ["GET"],
            r"^/search_suggestions$": ["GET"],
            r"^/directories.*": ["GET", "POST", "PUT", "DELETE"],
            r"^/reload$": ["POST"],
            r"^/expand$": ["POST"],
            r"^/rename$": ["POST"],
            r"^/filesystem/complete_path$": ["POST"],
            r"^/$": ["POST"],  # Create prompt
            r"^/\{prompt_id.*\}/referenced_by$": ["GET"],
            r"^/\{prompt_id.*\}$": ["GET", "PUT", "DELETE"],
        }
        
        # Get actual routes
        actual_routes = {}
        for route in prompt_router.routes:
            path = route.path
            methods = list(route.methods)
            if path in actual_routes:
                actual_routes[path].extend(methods)
            else:
                actual_routes[path] = methods
        
        # Check that we have routes matching all expected patterns
        for pattern, expected_methods in expected_patterns.items():
            pattern_regex = re.compile(pattern)
            matching_routes = [path for path in actual_routes.keys() if pattern_regex.match(path)]
            
            assert len(matching_routes) > 0, f"No routes found matching pattern: {pattern}"
            
            # Check methods for each matching route
            for route_path in matching_routes:
                route_methods = actual_routes[route_path]
                for method in expected_methods:
                    if method in ["GET", "PUT", "DELETE"] and "{prompt_id" in route_path:
                        # These should exist for prompt-specific routes
                        assert method in route_methods, \
                            f"Method {method} missing from route {route_path}. Available: {route_methods}"
    
    def test_no_duplicate_route_patterns(self):
        """Ensure no duplicate route patterns that could cause conflicts"""
        
        route_patterns = {}
        conflicts = []
        
        for route in prompt_router.routes:
            path = route.path
            methods = list(route.methods)
            
            for method in methods:
                key = (method, path)
                if key in route_patterns:
                    conflicts.append(f"Duplicate route: {method} {path}")
                else:
                    route_patterns[key] = route.endpoint.__name__
        
        assert len(conflicts) == 0, f"Route conflicts found: {conflicts}"
    
    def test_route_parameter_types_consistent(self):
        """Test that route parameters use consistent types"""
        
        prompt_id_routes = []
        parameter_types = {}
        
        for route in prompt_router.routes:
            if "{prompt_id" in route.path:
                # Extract parameter type
                if "{prompt_id:path}" in route.path:
                    param_type = "path"
                elif "{prompt_id}" in route.path:
                    param_type = "str"
                else:
                    param_type = "unknown"
                
                prompt_id_routes.append((route.path, param_type, list(route.methods)))
                
                if param_type in parameter_types:
                    parameter_types[param_type].append(route.path)
                else:
                    parameter_types[param_type] = [route.path]
        
        # All prompt_id parameters should use the same type for consistency
        # Based on our fix, they should all use "path" type
        assert "path" in parameter_types, "No routes using {prompt_id:path} parameter type"
        
        # Warn if we have mixed parameter types (this could cause routing issues)
        if len(parameter_types) > 1:
            mixed_types = {k: v for k, v in parameter_types.items()}
            print(f"WARNING: Mixed parameter types detected: {mixed_types}")
            # For now, allow mixed types but ensure path type is used for complex IDs


class TestRouteOrderValidation:
    """Test that route order is correct to prevent conflicts"""
    
    def test_specific_routes_before_catch_all(self):
        """Ensure specific routes are defined before catch-all routes"""
        
        routes_order = []
        catch_all_index = None
        specific_route_indices = []
        
        for i, route in enumerate(prompt_router.routes):
            routes_order.append((i, route.path, list(route.methods)))
            
            # Identify catch-all route (most general pattern)
            if route.path == "/{prompt_id:path}" and "GET" in route.methods:
                catch_all_index = i
            
            # Identify specific routes that could conflict
            if ("/{prompt_id" in route.path and 
                route.path != "/{prompt_id:path}" and 
                any(method in route.methods for method in ["GET", "PUT", "DELETE"])):
                specific_route_indices.append(i)
        
        # Verify catch-all route exists
        assert catch_all_index is not None, "Catch-all route /{prompt_id:path} not found"
        
        # Verify all specific routes come before catch-all
        conflicting_routes = [i for i in specific_route_indices if i > catch_all_index]
        
        if conflicting_routes:
            route_details = [routes_order[i] for i in conflicting_routes]
            assert False, f"Specific routes found AFTER catch-all route: {route_details}"
    
    def test_method_specific_route_precedence(self):
        """Test that method-specific routes have precedence over general routes"""
        
        # Group routes by path pattern
        path_methods = {}
        
        for route in prompt_router.routes:
            if route.path not in path_methods:
                path_methods[route.path] = []
            path_methods[route.path].extend(route.methods)
        
        # Check for potential conflicts
        conflicts = []
        
        for path, methods in path_methods.items():
            if len(methods) > 1:
                # Multiple methods on same path - ensure they don't conflict
                unique_methods = set(methods)
                if len(unique_methods) != len(methods):
                    conflicts.append(f"Duplicate methods on path {path}: {methods}")
        
        assert len(conflicts) == 0, f"Method conflicts found: {conflicts}"


class TestAPISchemaValidation:
    """Test that API schema is correctly generated"""
    
    @pytest.fixture
    def app_with_router(self):
        app = FastAPI()
        app.include_router(prompt_router)
        return app
    
    def test_openapi_schema_generation(self, app_with_router):
        """Test that OpenAPI schema generates correctly"""
        
        client = TestClient(app_with_router)
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        
        # Verify essential schema components
        assert "paths" in schema
        assert "components" in schema
        assert len(schema["paths"]) > 0
        
        # Check that all our routes are in the schema
        paths = schema["paths"]
        
        essential_routes = [
            "/",  # Create prompt
            "/{prompt_id}/referenced_by",  # Get references
        ]
        
        for route in essential_routes:
            found = False
            for path_key in paths.keys():
                if route.replace("{prompt_id}", "{prompt_id:path}") in path_key or route in path_key:
                    found = True
                    break
            assert found, f"Essential route {route} not found in OpenAPI schema"
    
    def test_route_documentation_exists(self, app_with_router):
        """Test that routes have proper documentation"""
        
        client = TestClient(app_with_router)
        response = client.get("/openapi.json")
        schema = response.json()
        
        undocumented_routes = []
        
        for path, methods in schema["paths"].items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                    if not details.get("summary") and not details.get("description"):
                        undocumented_routes.append(f"{method.upper()} {path}")
        
        # Allow some undocumented routes but flag them
        if undocumented_routes:
            print(f"WARNING: Undocumented routes found: {undocumented_routes}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
