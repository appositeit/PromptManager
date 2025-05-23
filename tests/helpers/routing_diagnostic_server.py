"""
Standalone FastAPI server for debugging and diagnosing routing configurations.

This server includes the main prompt API router (`src.api.router`)
and provides a comprehensive `/debug/routes` endpoint that lists all
registered routes, including grouped views. It is intended to be run
when troubleshooting routing issues or to understand how routes are
structured in the application. It also includes an `/exit` endpoint
for programmatically stopping the server.

Endpoints provided by this server:
- Routes from `src.api.router.router` (e.g., /api/prompts/...)
- / (simple health check message)
- /debug/routes (detailed list of all routes, including grouped by prefix)
- /exit (shuts down the server)
"""

import os
import sys
from pathlib import Path
import signal # For the /exit endpoint

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles # Kept for consistency
from fastapi.templating import Jinja2Templates # Kept for consistency
import uvicorn

# Add project root to sys.path to resolve src.* imports
# Assumes this script is in tests/helpers/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Create the FastAPI app
app = FastAPI(title="Routing Diagnostic Server")

# Base directory for static/templates
src_dir = project_root / "src"
static_dir = src_dir / "static"
templates_dir = src_dir / "templates"

# Set up static files (optional, but can help if router has static dependencies)
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"Notice: Static directory {static_dir} not found, not mounting.")

# Set up templates (optional)
if templates_dir.is_dir():
    templates = Jinja2Templates(directory=templates_dir)
else:
    print(f"Notice: Templates directory {templates_dir} not found, not setting up templates.")

# Import the router
try:
    from src.api.router import router as prompt_router
    print("Successfully imported prompt_router from src.api.router")
except ImportError as e:
    print(f"Warning: Could not import prompt_router from src.api.router: {e}. Main API routes might not be available.")
    prompt_router = None

# Include the router if imported
if prompt_router:
    app.include_router(prompt_router)
    print("Included prompt_router.")
else:
    print("Prompt router not included as it failed to import.")

# Root route
@app.get("/")
async def root(request: Request):
    """Root route for the diagnostic server."""
    return {"message": "Routing Diagnostic Server is running. Check /debug/routes for details."}

# Debug routes
@app.get("/debug/routes")
async def debug_all_routes(): # Renamed to avoid potential clashes
    """Debug endpoint to list all routes with details."""
    routes_details = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", str(route)),
            "name": getattr(route, "name", None),
            "methods": list(getattr(route, "methods", [])), # Ensure methods is a list for JSON
            "endpoint_name": getattr(getattr(route, "endpoint", None), "__name__", str(getattr(route, "endpoint", None)))
        }
        routes_details.append(route_info)
    
    # Group routes by the first path segment (prefix-like)
    grouped_routes = {}
    for route_detail in routes_details:
        path = route_detail["path"]
        # Handle potential leading slash and empty segments
        segments = [seg for seg in path.split("/") if seg]
        prefix = segments[0] if segments else "root"
        
        if prefix not in grouped_routes:
            grouped_routes[prefix] = []
        grouped_routes[prefix].append(route_detail)
    
    return {
        "all_routes": routes_details,
        "grouped_by_prefix": grouped_routes,
        "total_count": len(routes_details)
    }

# Exit route
@app.get("/exit")
async def exit_server_route(): # Renamed to avoid clash
    """Endpoint to gracefully shut down the server."""
    print("Exit endpoint called - shutting down server...")
    # A more robust way to stop uvicorn might be needed for programmatic shutdown
    # For a simple diagnostic server, os.kill is often sufficient for manual use.
    # Note: This will abruptly terminate the process.
    os.kill(os.getpid(), signal.SIGTERM)
    return {"success": True, "message": "Server is shutting down"} # This response might not be sent

if __name__ == "__main__":
    print("Starting Routing Diagnostic Server on http://127.0.0.1:8083")
    print("Access /debug/routes to see all configured routes.")
    print("Access /exit to stop the server.")
    uvicorn.run(app, host="127.0.0.1", port=8083) 