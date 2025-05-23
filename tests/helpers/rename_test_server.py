"""
Standalone FastAPI server for testing prompt management functionalities,
particularly rename operations.

This server includes the main prompt API router (`src.api.router`)
and basic page rendering for the prompt management UI. It is intended
to be run as a target for other test scripts or manual testing of
API endpoints related to prompts.

Endpoints provided by this server:
- Routes from `src.api.router.router` (e.g., /api/prompts/...)
- / (redirects to /manage/prompts)
- /manage/prompts (renders manage_prompts.html)
- /prompts/{prompt_id} (renders prompt_editor.html)
- /debug/routes (lists all available routes)
"""

import sys
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from src.api.router import router as prompt_router

# Add the project root to the Python path to resolve src.* imports
# Assumes this script is in tests/helpers/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Create app
app = FastAPI()

# Add the prompt router
app.include_router(prompt_router)

# Set up static files and templates relative to project root/src
# Corrected paths assuming this file is in tests/helpers/
static_dir = project_root / "src" / "static"
templates_dir = project_root / "src" / "templates"

print(f"Static dir: {static_dir}")
print(f"Templates dir: {templates_dir}")

# Mount static files
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"Warning: Static directory not found at {static_dir}")

# Set up templates
if templates_dir.is_dir():
    templates = Jinja2Templates(directory=templates_dir)
else:
    print(f"Warning: Templates directory not found at {templates_dir}")
    # Provide a dummy templates object if directory not found, to avoid crashing
    # and allow server to start for API testing at least.
    class DummyTemplates:
        def TemplateResponse(self, name, context):
            raise RuntimeError(f"Templates directory {templates_dir} not found. Cannot render {name}.")
    templates = DummyTemplates()

# Main route - redirect to the prompt management page
@app.get("/")
async def index(request: Request):
    """Redirect to the prompt management page."""
    return RedirectResponse(url="/manage/prompts")

# Prompt management
@app.get("/manage/prompts")
async def manage_prompts(request: Request):
    """Render the prompt management page."""
    try:
        return templates.TemplateResponse("manage_prompts.html", {"request": request})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route for prompt editor
@app.get("/prompts/{prompt_id}")
async def prompt_editor(request: Request, prompt_id: str):
    """Render the prompt editor page."""
    try:
        # Simplified for test server: real server has more logic to fetch prompt
        return templates.TemplateResponse(
            "prompt_editor.html",
            {"request": request, "prompt_id": prompt_id, "prompt": {"id": prompt_id, "content": "Test content"} }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Debug endpoint to list routes
@app.get("/debug/routes")
async def debug_routes():
    """List all routes in the application."""
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", ["GET"])
            methods_str = ", ".join([str(m) for m in methods])
            routes.append({
                "path": route.path,
                "name": getattr(route, "name", "N/A"),
                "methods": methods_str
            })
    return {"routes": routes}

# Run the server
if __name__ == "__main__":
    import uvicorn
    
    # Debug mode with route information
    print("Available routes:")
    for route_info in debug_routes.__annotations__['return'](app.routes):
        print(f"  {route_info['methods']:<20} {route_info['path']} (Name: {route_info['name']})")
    
    uvicorn.run(app, host="127.0.0.1", port=8082) 