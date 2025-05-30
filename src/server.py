"""
FastAPI application for the Prompt Manager system.

This module provides a FastAPI application that serves the prompt management
interface and API.
"""

import sys
from pathlib import Path
from typing import Optional, Callable, Coroutine, Any

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
# from services.prompt_service import PromptService # Old import on line 33, now removed/commented
from src.services.prompt_service import PromptService as PromptServiceClass # Changed import
from src.services.filesystem_service import FilesystemService

# Get the base path and add to sys.path to ensure imports work
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Print Python path for debugging
print(f"Python path in server.py: {sys.path}")

# Global prompt service instance - initialized lazily
prompt_service_instance: Optional[PromptServiceClass] = None

def _get_or_create_global_prompt_service() -> Optional[PromptServiceClass]:
    """Get or create the global PromptService instance."""
    global prompt_service_instance
    
    if prompt_service_instance is None:
        try:
            prompt_service_instance = PromptServiceClass(base_directories=None, auto_load=True)
            logger.info("Global PromptService instance initialized.")
            
            # Set up websocket store
            try:
                import src.api.websocket_routes as ws_routes_module
                ws_routes_module.websocket_prompt_service_store = prompt_service_instance
                logger.info("Successfully set websocket_prompt_service_store in websocket_routes.")
            except Exception as e_set_store:
                logger.error(f"Failed to set websocket_prompt_service_store: {e_set_store}", exc_info=True)
                
        except Exception as e_init:
            logger.error(f"CRITICAL: Failed to initialize PromptService instance: {e_init}", exc_info=True)
            prompt_service_instance = None
    
    return prompt_service_instance

# Now that prompt_service_instance is defined, we can import routers that might use it (via dependency injection)
try:
    # These will likely fail if BASE_DIR is not on sys.path
    from src.api.session_routes import router as session_router
    from src.api.router import router as prompt_router 
    from src.api.fragments_router_redirect import router as fragments_router_redirect
    from src.api.websocket_routes import router as websocket_router
    from src.api.unified_router import router as unified_prompt_router
    from src.api.mcp_router import router as mcp_router
    print("Attempted direct api.* import paths for routers")
except ImportError as e_direct:
    print(f"Direct api.* import failed ({e_direct}), trying src.api.*")
    try:
        from src.api.session_routes import router as session_router
        from src.api.router import router as prompt_router 
        from src.api.fragments_router_redirect import router as fragments_router_redirect
        from src.api.websocket_routes import router as websocket_router
        from src.api.unified_router import router as unified_prompt_router
        from src.api.mcp_router import router as mcp_router
        print("Using src.api.* import paths for routers")
    except ImportError as e_src:
        print(f"CRITICAL Error importing routers via src.api.* ({e_src}). Some API functionality will be missing.")
        from fastapi import APIRouter
        session_router = APIRouter()
        prompt_router = APIRouter(prefix="/api/prompts", tags=["prompts"])
        fragments_router_redirect = APIRouter(prefix="/api/fragments", tags=["fragments"])
        websocket_router = APIRouter(prefix="/ws", tags=["websockets"])
        unified_prompt_router = APIRouter(prefix="/api/unified", tags=["unified"])
        mcp_router = APIRouter(prefix="/api/mcp", tags=["mcp"])

# After importing routers, add:
try:
    from src.api.websocket_debug import router as websocket_debug_router
except ImportError:
    websocket_debug_router = None

# Create the FastAPI app
app = FastAPI(
    title="Prompt Manager",
    description="API for managing AI prompts with composable elements",
    version="0.1.0"
)

# Dependency override for PromptService
async def get_global_prompt_service() -> Optional[PromptServiceClass]: # Use Class here
    return _get_or_create_global_prompt_service()

# Import the dependency placeholder from the API router module
api_prompt_service_dependency_placeholder: Optional[Callable[[], Coroutine[Any, Any, PromptServiceClass]]] = None
try:
    from src.api.router import get_prompt_service_dependency # Import directly
    api_prompt_service_dependency_placeholder = get_prompt_service_dependency # Assign to the correctly typed variable
    logger.info("Successfully imported get_prompt_service_dependency from src.api.router and assigned to placeholder")
except ImportError as e:
    # api_prompt_service_dependency_placeholder remains None, already declared and typed
    logger.error(f"Failed to import get_prompt_service_dependency from src.api.router: {e}")

# Import WebSocket dependency placeholder (NO LONGER NEEDED FOR OVERRIDE)
# ws_dependency_placeholder = None 
# try:
#     from src.api.websocket_routes import get_ws_prompt_service as ws_placeholder
#     ws_dependency_placeholder = ws_placeholder
#     logger.info("Successfully imported ws_dependency_placeholder from src.api.websocket_routes.")
# except ImportError as e:
#     logger.error(f"Failed to import ws_dependency_placeholder from src.api.websocket_routes: {e}")

if api_prompt_service_dependency_placeholder:
    app.dependency_overrides[api_prompt_service_dependency_placeholder] = get_global_prompt_service
    logger.info("FastAPI dependency_overrides configured for PromptService (API Router).")
else:
    logger.warning("API PromptService dependency placeholder not found. API override not configured.")

# WebSocket PromptService is now handled by direct injection into websocket_routes module.
# The standard dependency override for WebSockets is removed due to persistent issues.

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(session_router)
app.include_router(prompt_router)
app.include_router(fragments_router_redirect)
app.include_router(websocket_router)
app.include_router(unified_prompt_router)
app.include_router(mcp_router)

if websocket_debug_router:
    app.include_router(websocket_debug_router)

@app.middleware("http")
async def websocket_cors_middleware(request: Request, call_next):
    if request.url.path.startswith(("/api/ws/", "/ws/prompts/")) and request.headers.get("upgrade", "").lower() == "websocket":
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/manage/prompts")

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered.")
    service = _get_or_create_global_prompt_service()
    if service:
        logger.info(f"PromptService initialized with {len(service.directories)} directorie(s) and {len(service.prompts)} prompt(s) loaded.")
        if not service.directories:
            logger.warning("Startup check: PromptService has no directories configured after __init__.")
        if not service.prompts and service.directories:
             logger.warning("Startup check: PromptService has directories but no prompts loaded.")
    else:
        logger.error("Application startup: Global PromptService instance is NOT available!")

@app.get("/manage/prompts", response_class=HTMLResponse)
async def manage_prompts(request: Request):
    return templates.TemplateResponse("manage_prompts.html", {"request": request})

@app.get("/prompts/{prompt_id:path}", response_class=HTMLResponse)
async def prompt_editor(request: Request, prompt_id: str):
    path_param_id = prompt_id
    service = _get_or_create_global_prompt_service()
    if not service:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Service Error",
            "message": "Prompt service is not available."
        }, status_code=500)
    
    # Try to find the prompt directly first
    prompt_object = service.get_prompt(path_param_id)
    
    # If not found and the ID contains spaces, try converting spaces to underscores
    if not prompt_object and ' ' in path_param_id:
        # Convert spaces to underscores and try again
        normalized_id = path_param_id.replace(' ', '_')
        prompt_object = service.get_prompt(normalized_id)
        if prompt_object:
            # Redirect to the correct URL to normalize the URL structure
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=f"/prompts/{normalized_id}", status_code=301)
    
    if not prompt_object:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Prompt Not Found",
            "message": f"The prompt with ID '{path_param_id}' could not be found."
        }, status_code=404)
    prompt_display_name = getattr(prompt_object, 'name', prompt_object.id)
    if prompt_object.id != path_param_id:
        logger.warning(f"Prompt ID mismatch: path param ID was '{path_param_id}', fetched '{prompt_object.id}'.")
    expanded_content, dependencies, warnings = service.expand_inclusions(
        prompt_object.content, parent_id=prompt_object.id
    )
    logger.debug(f"Rendering prompt_editor.html for '{path_param_id}'")
    return templates.TemplateResponse("prompt_editor.html", {
        "request": request,
        "prompt": prompt_object,
        "template_safe_prompt_id": path_param_id,
        "actual_unique_id": prompt_object.unique_id,
        "expanded_content": expanded_content,
        "dependencies": list(dependencies),
        "warnings": warnings,
        "title": f"Edit: {prompt_display_name or path_param_id}"
    })

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse("error.html", {
        "request": request, 
        "title": "Error 404", 
        "message": "The requested page was not found.", 
        "details": str(exc)
    }, status_code=404)

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc):
    logger.error(f"Server error: {exc}", exc_info=True)
    return templates.TemplateResponse("error.html", {
        "request": request, 
        "title": "Error 500 - Internal Server Error", 
        "message": "An unexpected error occurred on the server.", 
        "details": str(exc) 
    }, status_code=500)

@app.get("/api/exit")
async def exit_server():
    logger.info("Received /api/exit command. Shutting down.")
    return {"success": True, "message": "Server is shutting down"}

# Create app function for testing
def create_app(config_path=None, fragment_dirs=None, template_dirs=None, port=8081):
    """Create the FastAPI app for testing."""
    if fragment_dirs:
        logger.info(f"create_app called with fragment_dirs for testing: {fragment_dirs}")
        test_prompt_service_instance = PromptServiceClass(base_directories=fragment_dirs, auto_load=True)
        logger.info(f"Created isolated PromptService for test_create_app. Base dirs: {fragment_dirs}")
        import src.api.websocket_routes as ws_routes_module
        ws_routes_module.websocket_prompt_service_store = test_prompt_service_instance
        test_app = FastAPI(title="Test Prompt Manager", version="0.1.0-test")
        def get_test_prompt_service() -> PromptServiceClass:
            return test_prompt_service_instance
        if api_prompt_service_dependency_placeholder:
            test_app.dependency_overrides[api_prompt_service_dependency_placeholder] = get_test_prompt_service
        test_app.include_router(prompt_router)
        test_app.include_router(session_router)
        test_app.include_router(websocket_router)
        if websocket_debug_router:
            test_app.include_router(websocket_debug_router)
        test_app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
        return test_app
    else:
        logger.info("create_app called without fragment_dirs, returning global app.")
        return app

# Main entry point for running the server directly
def main(args=None):
    import uvicorn
    import argparse
    
    if args is None:
        parser = argparse.ArgumentParser(description='Prompt Manager Server')
        parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
        parser.add_argument('--port', type=int, default=8081, help='Port to bind to (default: 8081)')
        parser.add_argument('--log-level', default='info', help='Log level (default: info)')
        args = parser.parse_args()
    
    host = args.host
    port = args.port
    log_level = args.log_level
    
    print(f"Starting Prompt Manager server on {host}:{port}")
    print(f"Log level: {log_level}")
    uvicorn.run("src.server:app", host=host, port=port, log_level=log_level, reload=False)

if __name__ == "__main__":
    main()