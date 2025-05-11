"""
FastAPI application for the Coordinator prompt and session management system.

This module provides a FastAPI application that serves the prompt management
and session management interfaces, as well as providing static assets.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from coordinator.prompts.api.session_views import router as session_router

# Get the base path
BASE_DIR = Path(__file__).resolve().parent

# Create the FastAPI app
app = FastAPI(
    title="Coordinator Prompt Manager",
    description="API for managing prompts and sessions in the Coordinator system",
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

# Include routers
app.include_router(session_router)

# Import the routers
from coordinator.prompts.api.router import router as prompt_router
from coordinator.prompts.api.unified_router import router as unified_prompt_router
from coordinator.prompts.api.mcp_router import router as mcp_router

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

# Root route
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the home page."""
    # Initialize prompt directories
    from coordinator.prompts.services.prompt_dirs import initialize_prompt_directories
    initialize_prompt_directories()
    
    return templates.TemplateResponse("home.html", {"request": request})

# Prompt management routes
@app.get("/manage/prompts", response_class=HTMLResponse)
async def manage_prompts(request: Request):
    """Render the prompt management page."""
    return templates.TemplateResponse("manage_prompts.html", {"request": request})

# MCP Servers routes - added multiple patterns to ensure it gets matched
@app.get("/mcp", response_class=HTMLResponse)
@app.get("/mcp/", response_class=HTMLResponse)
async def mcp_servers(request: Request):
    """Render the MCP servers management page."""
    return templates.TemplateResponse("mcp_servers.html", {"request": request})

# Settings route
@app.get("/settings", response_class=HTMLResponse)
@app.get("/settings/", response_class=HTMLResponse)
async def settings(request: Request):
    """Render the settings page."""
    return templates.TemplateResponse("settings.html", {"request": request})

# Session routes
@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session(request: Request, session_id: str):
    """Render the session page."""
    return templates.TemplateResponse("session.html", {"request": request, "session_id": session_id})

@app.get("/sessions/{session_id}/workers/{worker_id}", response_class=HTMLResponse)
async def worker_session(request: Request, session_id: str, worker_id: int):
    """Render the worker session page."""
    return templates.TemplateResponse("session.html", {"request": request, "session_id": session_id, "worker_id": worker_id})

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
    
    parser = argparse.ArgumentParser(description="Coordinator Prompt Manager")
    
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host to bind the server to")
    
    parser.add_argument("--port", type=int, default=8081,
                        help="Port to bind the server to")
    
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "coordinator.prompts.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
