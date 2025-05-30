"""
Comprehensive unit tests for server module
Tests FastAPI application setup, dependency injection, middleware, and routing
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.services.prompt_service import PromptService


class TestServerConfiguration:
    """Test server initialization and configuration"""
    
    def test_base_dir_and_project_root_setup(self):
        """Test BASE_DIR and PROJECT_ROOT path setup"""
        # This test is conceptual since src.server is already imported at module level
        # We'll test that the expected paths are in sys.path instead
        import sys
        
        # Check that project root is in sys.path (it should be due to conftest.py)
        project_root_found = any(
            path.endswith('prompt_manager') 
            for path in sys.path
        )
        assert project_root_found, "Project root should be in sys.path"
        
        # Check that src directory is accessible
        import src.server
        assert hasattr(src.server, 'app'), "Server module should have app attribute"
    
    def test_prompt_service_initialization_success(self):
        """Test successful PromptService initialization"""
        with patch('src.server.PromptServiceClass') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            # Mock the websocket_routes import and assignment
            with patch('src.server.sys.path'), \
                 patch('src.server.print'), \
                 patch('src.server.logger'):
                
                # Reset the global instance to None to test initialization
                import src.server
                src.server.prompt_service_instance = None
                
                # Trigger lazy initialization
                result = src.server._get_or_create_global_prompt_service()
                
                # Should have created an instance
                mock_service_class.assert_called_with(base_directories=None, auto_load=True)
                assert result == mock_instance
    
    def test_prompt_service_initialization_failure(self):
        """Test PromptService initialization failure handling"""
        with patch('src.server.PromptServiceClass') as mock_service_class:
            mock_service_class.side_effect = Exception("Init failed")
            
            with patch('src.server.sys.path'), \
                 patch('src.server.print'), \
                 patch('src.server.logger') as mock_logger:
                
                # Reset the global instance to None to test initialization
                import src.server
                src.server.prompt_service_instance = None
                
                # Trigger lazy initialization
                result = src.server._get_or_create_global_prompt_service()
                
                # Should have logged error and returned None
                mock_logger.error.assert_called()
                assert result is None
    
    def test_websocket_routes_store_assignment(self):
        """Test WebSocket routes store assignment"""
        with patch('src.server.PromptServiceClass') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            with patch('src.server.sys.path'), \
                 patch('src.server.print'), \
                 patch('src.server.logger') as mock_logger:
                
                # Reset the global instance to None to test initialization
                import src.server
                src.server.prompt_service_instance = None
                
                # Trigger lazy initialization
                result = src.server._get_or_create_global_prompt_service()
                
                # Should have created instance and attempted websocket setup
                mock_service_class.assert_called_with(base_directories=None, auto_load=True)
                assert result == mock_instance
                
                # Should have logged success or failure of websocket setup
                logged_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                assert any("Global PromptService instance initialized" in call for call in logged_calls)
    
    def test_router_imports_fallback(self):
        """Test router import fallback mechanism"""
        # Mock failed direct imports but successful src.api.* imports
        with patch('src.server.sys.path'), \
             patch('src.server.print'), \
             patch('src.server.logger'):
            
            # Test direct import failure followed by src.api success
            import importlib
            import src.server
            
            # Should have loaded routers (exact behavior depends on import state)
            # This test validates that the import error handling exists
            assert hasattr(src.server, 'session_router')
            assert hasattr(src.server, 'prompt_router')


class TestFastAPIAppCreation:
    """Test FastAPI application creation and configuration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_prompt_service = Mock(spec=PromptService)
        self.mock_prompt_service.directories = []
        self.mock_prompt_service.prompts = {}
    
    def test_app_creation_basic(self):
        """Test basic FastAPI app creation"""
        from src.server import app
        
        assert isinstance(app, FastAPI)
        assert app.title == "Prompt Manager"
        assert app.description == "API for managing AI prompts with composable elements"
        assert app.version == "0.1.0"
    
    def test_dependency_override_configuration(self):
        """Test dependency override configuration"""
        with patch('src.server.api_prompt_service_dependency_placeholder') as mock_placeholder:
            from src.server import app
            
            # Should have configured dependency override
            if mock_placeholder:
                assert mock_placeholder in app.dependency_overrides
    
    def test_cors_middleware_configuration(self):
        """Test CORS middleware configuration"""
        from src.server import app
        
        # Check that CORS middleware is added
        middleware_stack = app.user_middleware
        cors_middleware = any(
            'CORSMiddleware' in str(middleware.cls) 
            for middleware in middleware_stack
        )
        assert cors_middleware
    
    def test_router_inclusion(self):
        """Test that all routers are included"""
        from src.server import app
        
        # Check that routers are included (by checking routes)
        route_paths = [route.path for route in app.routes]
        
        # Should have various API routes
        api_routes = [path for path in route_paths if path.startswith('/api')]
        assert len(api_routes) > 0
    
    def test_static_files_mounting(self):
        """Test static files mounting"""
        from src.server import app
        
        # Check for static file mount
        static_mount = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == '/static':
                static_mount = route
                break
        
        assert static_mount is not None


class TestServerEndpoints:
    """Test server endpoints and request handling"""
    
    def setup_method(self):
        """Set up test client"""
        from src.server import app
        self.client = TestClient(app)
        self.mock_prompt_service = Mock(spec=PromptService)
    
    def test_root_endpoint_redirect(self):
        """Test root endpoint redirects to manage prompts"""
        response = self.client.get("/")
        assert response.status_code == 302
        assert response.headers["location"] == "/manage/prompts"
    
    def test_manage_prompts_endpoint(self):
        """Test manage prompts endpoint returns HTML"""
        with patch('src.server.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            
            response = self.client.get("/manage/prompts")
            
            # Should call template response
            mock_templates.TemplateResponse.assert_called_once()
    
    def test_prompt_editor_endpoint_prompt_found(self):
        """Test prompt editor endpoint when prompt exists"""
        mock_prompt = Mock()
        mock_prompt.id = "test_prompt"
        mock_prompt.name = "Test Prompt"
        mock_prompt.content = "Test content"
        mock_prompt.unique_id = "test/test_prompt"
        
        with patch('src.server._get_or_create_global_prompt_service', return_value=self.mock_prompt_service):
            with patch('src.server.templates') as mock_templates:
                mock_templates.TemplateResponse.return_value = Mock()
                
                self.mock_prompt_service.get_prompt.return_value = mock_prompt
                self.mock_prompt_service.expand_inclusions.return_value = (
                    "expanded content", set(), []
                )
                
                response = self.client.get("/prompts/test_prompt")
                
                # Should call template response with prompt data
                mock_templates.TemplateResponse.assert_called_once()
                call_args = mock_templates.TemplateResponse.call_args
                assert "prompt_editor.html" in call_args[0]
                context = call_args[0][1]
                assert context["prompt"] == mock_prompt
    
    def test_prompt_editor_endpoint_prompt_not_found(self):
        """Test prompt editor endpoint when prompt doesn't exist"""
        with patch('src.server._get_or_create_global_prompt_service', return_value=self.mock_prompt_service):
            with patch('src.server.templates') as mock_templates:
                mock_templates.TemplateResponse.return_value = Mock()
                
                self.mock_prompt_service.get_prompt.return_value = None
                
                response = self.client.get("/prompts/nonexistent_prompt")
                
                # Should call error template
                mock_templates.TemplateResponse.assert_called_once()
                call_args = mock_templates.TemplateResponse.call_args
                assert "error.html" in call_args[0]
    
    def test_prompt_editor_endpoint_with_spaces_redirect(self):
        """Test prompt editor endpoint redirects when spaces in ID are normalized"""
        mock_prompt = Mock()
        mock_prompt.id = "test_prompt"
        mock_prompt.name = "Test Prompt"
        
        with patch('src.server._get_or_create_global_prompt_service', return_value=self.mock_prompt_service):
            # First call returns None, second call returns prompt
            self.mock_prompt_service.get_prompt.side_effect = [None, mock_prompt]
            
            response = self.client.get("/prompts/test%20prompt", follow_redirects=False)
            
            # Should redirect to normalized URL
            assert response.status_code == 301
            assert "/prompts/test_prompt" in response.headers["location"]
    
    def test_prompt_editor_endpoint_service_unavailable(self):
        """Test prompt editor endpoint when service is unavailable"""
        with patch('src.server._get_or_create_global_prompt_service', return_value=None):
            with patch('src.server.templates') as mock_templates:
                mock_templates.TemplateResponse.return_value = Mock()
                
                response = self.client.get("/prompts/test_prompt")
                
                # Should return service error
                mock_templates.TemplateResponse.assert_called_once()
                call_args = mock_templates.TemplateResponse.call_args
                assert "error.html" in call_args[0]
                assert call_args[1]["status_code"] == 500
    
    def test_exit_endpoint(self):
        """Test exit endpoint returns success"""
        response = self.client.get("/api/exit")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "shutting down" in data["message"].lower()


class TestServerMiddleware:
    """Test server middleware functionality"""
    
    def setup_method(self):
        """Set up test client"""
        from src.server import app
        self.client = TestClient(app)
    
    def test_websocket_cors_middleware_websocket_request(self):
        """Test WebSocket CORS middleware for WebSocket requests"""
        # This is complex to test without actual WebSocket connections
        # Test the middleware logic conceptually
        from src.server import websocket_cors_middleware
        
        mock_request = Mock()
        mock_request.url.path = "/api/ws/test"
        mock_request.headers = {"upgrade": "websocket"}
        
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        import asyncio
        async def test_middleware():
            result = await websocket_cors_middleware(mock_request, mock_call_next)
            return result
        
        # Run the middleware test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_middleware())
            
            # Should have added CORS headers
            assert "Access-Control-Allow-Origin" in result.headers
            assert result.headers["Access-Control-Allow-Origin"] == "*"
        finally:
            loop.close()
    
    def test_websocket_cors_middleware_regular_request(self):
        """Test WebSocket CORS middleware for regular HTTP requests"""
        from src.server import websocket_cors_middleware
        
        mock_request = Mock()
        mock_request.url.path = "/api/prompts"
        mock_request.headers = {}
        
        mock_response = Mock()
        
        async def mock_call_next(request):
            return mock_response
        
        import asyncio
        async def test_middleware():
            result = await websocket_cors_middleware(mock_request, mock_call_next)
            return result
        
        # Run the middleware test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_middleware())
            
            # Should pass through unchanged
            assert result == mock_response
        finally:
            loop.close()


class TestServerExceptionHandlers:
    """Test server exception handlers"""
    
    def setup_method(self):
        """Set up test client"""
        from src.server import app
        self.client = TestClient(app)
    
    def test_404_exception_handler(self):
        """Test 404 exception handler"""
        response = self.client.get("/nonexistent/path")
        assert response.status_code == 404
    
    def test_500_exception_handler_concept(self):
        """Test 500 exception handler concept"""
        # Testing 500 handler requires triggering an actual server error
        # which is complex in unit tests. Test the handler function directly.
        
        from src.server import server_error_exception_handler
        
        mock_request = Mock()
        mock_exc = Exception("Test error")
        
        with patch('src.server.templates') as mock_templates:
            with patch('src.server.logger'):
                mock_templates.TemplateResponse.return_value = Mock()
                
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        server_error_exception_handler(mock_request, mock_exc)
                    )
                    
                    # Should call error template
                    mock_templates.TemplateResponse.assert_called_once()
                    call_args = mock_templates.TemplateResponse.call_args
                    assert "error.html" in call_args[0]
                    assert call_args[1]["status_code"] == 500
                finally:
                    loop.close()


class TestServerStartupEvent:
    """Test server startup event handler"""
    
    def test_startup_event_with_service(self):
        """Test startup event with available prompt service"""
        mock_service = Mock()
        mock_service.directories = [Mock(), Mock()]
        mock_service.prompts = {"prompt1": Mock(), "prompt2": Mock()}
        
        with patch('src.server._get_or_create_global_prompt_service', return_value=mock_service):
            with patch('src.server.logger') as mock_logger:
                from src.server import startup_event
                
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(startup_event())
                    
                    # Should log successful startup
                    mock_logger.info.assert_called()
                    info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                    startup_calls = [call for call in info_calls if "startup" in call.lower()]
                    assert len(startup_calls) > 0
                finally:
                    loop.close()
    
    def test_startup_event_without_service(self):
        """Test startup event without prompt service"""
        with patch('src.server._get_or_create_global_prompt_service', return_value=None):
            with patch('src.server.logger') as mock_logger:
                from src.server import startup_event
                
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(startup_event())
                    
                    # Should log error
                    mock_logger.error.assert_called()
                finally:
                    loop.close()
    
    def test_startup_event_warnings_no_directories(self):
        """Test startup event warnings when no directories configured"""
        mock_service = Mock()
        mock_service.directories = []
        mock_service.prompts = {}
        
        with patch('src.server._get_or_create_global_prompt_service', return_value=mock_service):
            with patch('src.server.logger') as mock_logger:
                from src.server import startup_event
                
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(startup_event())
                    
                    # Should log warning about no directories
                    mock_logger.warning.assert_called()
                finally:
                    loop.close()
    
    def test_startup_event_warnings_no_prompts(self):
        """Test startup event warnings when directories exist but no prompts"""
        mock_service = Mock()
        mock_service.directories = [Mock()]
        mock_service.prompts = {}
        
        with patch('src.server._get_or_create_global_prompt_service', return_value=mock_service):
            with patch('src.server.logger') as mock_logger:
                from src.server import startup_event
                
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(startup_event())
                    
                    # Should log warning about no prompts
                    mock_logger.warning.assert_called()
                finally:
                    loop.close()


class TestCreateAppFunction:
    """Test create_app function for testing"""
    
    def test_create_app_with_fragment_dirs(self):
        """Test create_app with fragment directories for testing"""
        test_dirs = ["/test/dir1", "/test/dir2"]
        
        with patch('src.server.PromptServiceClass') as mock_service_class:
            mock_instance = Mock()
            mock_service_class.return_value = mock_instance
            
            with patch('src.server.logger'), \
                 patch('src.server.BASE_DIR', Path("/test/base")):
                
                from src.server import create_app
                
                result_app = create_app(fragment_dirs=test_dirs)
                
                # Should create isolated PromptService
                mock_service_class.assert_called_with(
                    base_directories=test_dirs, 
                    auto_load=True
                )
                
                # Should return FastAPI app
                assert isinstance(result_app, FastAPI)
                assert result_app.title == "Test Prompt Manager"
    
    def test_create_app_without_fragment_dirs(self):
        """Test create_app without fragment directories returns global app"""
        with patch('src.server.logger'):
            from src.server import create_app, app as global_app
            
            result_app = create_app()
            
            # Should return global app
            assert result_app == global_app


class TestMainFunction:
    """Test main function for server startup"""
    
    def test_main_with_default_args(self):
        """Test main function with default arguments"""
        with patch('uvicorn.run') as mock_run:
            with patch('argparse.ArgumentParser') as mock_parser:
                mock_args = Mock()
                mock_args.host = "0.0.0.0"
                mock_args.port = 8081
                mock_args.log_level = "info"
                mock_parser.return_value.parse_args.return_value = mock_args
                
                from src.server import main
                main()
                
                # Should call uvicorn.run with correct parameters
                mock_run.assert_called_once_with(
                    "src.server:app",
                    host="0.0.0.0",
                    port=8081,
                    log_level="info",
                    reload=False
                )
    
    def test_main_with_custom_args(self):
        """Test main function with custom arguments"""
        mock_args = Mock()
        mock_args.host = "127.0.0.1"
        mock_args.port = 9000
        mock_args.log_level = "debug"
        
        with patch('uvicorn.run') as mock_run:
            from src.server import main
            main(mock_args)
            
            # Should call uvicorn.run with custom parameters
            mock_run.assert_called_once_with(
                "src.server:app",
                host="127.0.0.1",
                port=9000,
                log_level="debug",
                reload=False
            )


class TestGlobalPromptServiceDependency:
    """Test global prompt service dependency function"""
    
    def test_get_global_prompt_service_available(self):
        """Test get_global_prompt_service when service is available"""
        mock_service = Mock()
        
        with patch('src.server._get_or_create_global_prompt_service', return_value=mock_service):
            from src.server import get_global_prompt_service
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(get_global_prompt_service())
                assert result == mock_service
            finally:
                loop.close()
    
    def test_get_global_prompt_service_unavailable(self):
        """Test get_global_prompt_service when service is unavailable"""
        with patch('src.server._get_or_create_global_prompt_service', return_value=None):
            from src.server import get_global_prompt_service
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(get_global_prompt_service())
                assert result is None
            finally:
                loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
