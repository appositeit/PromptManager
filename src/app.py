"""
FastAPI application for the Prompt Manager system.

This module provides a FastAPI application that serves the prompt management
interface and API.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from api.session_routes import router as session_router

# Get the base path
BASE_DIR = Path(__file__).resolve().parent

# Create the FastAPI app
app = FastAPI(
    title="Prompt Manager",
    description="API for managing AI prompts with composable elements",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include API routers
app.include_router(session_router)

# Import the routers
from api.router import router as prompt_router
from api.unified_router import router as unified_prompt_router
from api.mcp_router import router as mcp_router
from api.fragments_router_redirect import router as fragments_router_redirect

# Include routers with error handling
try:
    app.include_router(prompt_router)
except Exception as e:
    print(f"Warning: Could not include prompt_router: {e}")

try:
    app.include_router(unified_prompt_router)
except Exception as e:
    print(f"Warning: Could not include unified_prompt_router: {e}")

try:
    app.include_router(mcp_router)
except Exception as e:
    print(f"Warning: Could not include mcp_router: {e}")

try:
    app.include_router(fragments_router_redirect)
except Exception as e:
    print(f"Warning: Could not include fragments_router_redirect: {e}")

# Root route - redirect to Manage Prompts page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to the Manage Prompts page."""
    # Initialize prompt directories
    from services.prompt_dirs import initialize_prompt_directories
    initialize_prompt_directories()
    
    # Redirect to the manage prompts page
    return RedirectResponse(url="/manage/prompts")

# Prompt management route
@app.get("/manage/prompts", response_class=HTMLResponse)
async def manage_prompts(request: Request):
    """Render the prompt management page."""
    # Initialize prompt directories
    from services.prompt_dirs import initialize_prompt_directories
    initialize_prompt_directories()
    
    return templates.TemplateResponse("manage_prompts.html", {"request": request})

# Error handlers
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    """Handle 404 errors."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 404,
            "error_message": "The requested page was not found."
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc):
    """Handle 500 errors."""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "Internal server error."
        },
        status_code=500
    )

# Main function to run the app directly
def main():
    """Run the FastAPI app using Uvicorn."""
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description="Prompt Manager")
    
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host to bind the server to")
    
    parser.add_argument("--port", type=int, default=8081,
                        help="Port to bind the server to")
    
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
