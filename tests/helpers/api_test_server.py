"""
Standalone FastAPI server for verifying the main API routes.

This server includes the primary prompt API router (`src.api.router`)
and is intended to be run as a target for testing API endpoints.
It can be used with tools like curl, Postman, or automated test
scripts that make HTTP requests to validate API behavior.

Endpoints provided by this server:
- Routes from `src.api.router.router` (e.g., /api/prompts/...)
- / (simple health check message)
- /debug/routes (lists all available routes from the included router)
"""

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # Kept for consistency, though not strictly used by API router
from fastapi.templating import Jinja2Templates # Kept for consistency

# Add project root to sys.path to resolve src.* imports
# Assumes this script is in tests/helpers/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
# Also add src to path, as some modules might do relative imports from src
# sys.path.insert(0, str(project_root / "src")) # Redundant if src. is used in imports

# Create the app
app = FastAPI(title="API Test Server")

# Base directory for static/templates, if they were to be used more extensively
# For an API-only test server, these might not be critical but good for completeness
src_dir = project_root / "src"
static_dir = src_dir / "static"
templates_dir = src_dir / "templates"

# Mount static files (optional for pure API testing server)
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"Notice: Static directory not found at {static_dir}, not mounting.")

# Set up templates (optional for pure API testing server)
if templates_dir.is_dir():
    templates = Jinja2Templates(directory=templates_dir)
else:
    print(f"Notice: Templates directory not found at {templates_dir}, not setting up templates.")

# Import the router
try:
    from src.api.router import router as prompt_router
    print("Successfully imported prompt_router from src.api.router")
except ImportError as e1:
    print(f"Failed to import prompt_router from src.api.router: {e1}")
    try:
        # Fallback if tests/helpers is added to PYTHONPATH somehow or CWD is project root
        from src.api.router import router as prompt_router # Changed to src.
        print("Successfully imported prompt_router from api.router (fallback)")
    except ImportError as e2:
        print(f"Error: Could not import prompt_router: {e2}. API routes will not be available.")
        prompt_router = None # Ensure it's defined
        # sys.exit(1) # Decided not to exit, server can still run for basic checks

# Include the router if successfully imported
if prompt_router:
    app.include_router(prompt_router)
    print(f"Included prompt_router. Prefixes: {[route.prefix for route in prompt_router.routes if hasattr(route, 'prefix')]}")
else:
    print("Prompt router was not imported, so it cannot be included.")

# Root route
@app.get("/")
async def root():
    return {"message": "API Test server is running. Check /debug/routes for API endpoints."}

# Debug route
@app.get("/debug/routes")
async def debug_api_routes(): # Renamed to avoid clash if other debug_routes exist
    """Debug endpoint to list all routes from the app."""
    routes_info = []
    if hasattr(app, "routes"):
        for route in app.routes:
            routes_info.append({
                "path": getattr(route, "path", str(route)),
                "name": getattr(route, "name", None),
                "methods": list(getattr(route, "methods", [])), # Convert to list for JSON
                "type": str(type(route).__name__)
            })
    
    # Print routes to console for immediate feedback when server starts
    print("\nAvailable routes on this API Test Server:")
    for route_detail in sorted(routes_info, key=lambda x: str(x["path"])):
        print(f"  Path: {route_detail['path']}, Name: {route_detail['name']}, Methods: {route_detail['methods']}")
    
    return {
        "routes": routes_info,
        "count": len(routes_info)
    }

if __name__ == "__main__":
    print("Starting API test server on http://127.0.0.1:8089")
    # Call debug_api_routes logic before uvicorn to print, as uvicorn might take over console
    # This is a bit of a hack; ideally, uvicorn logging would be configured.
    # For now, let's rely on the print within the endpoint if accessed via browser/curl.
    uvicorn.run(app, host="127.0.0.1", port=8089) 