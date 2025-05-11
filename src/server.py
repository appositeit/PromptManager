"""
Main server application for the prompt management system.

This module provides a FastAPI application for the prompt management
system, serving both the API and the web interface.
"""

import os
import sys
import asyncio
import traceback
from typing import Optional
from pathlib import Path
import argparse
import uvicorn
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import logging

from src.api.unified_router import router as api_router
from src.api.session_routes import router as session_router
from src.services.prompt_service import PromptService
from src.models.unified_prompt import Prompt, PromptType


# Set up logging
def setup_logging(log_file: str = None):
    """Set up logging configuration."""
    # Remove default logger
    logger.remove()
    
    # Configure loguru
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    # Add console logger
    logger.add(sys.stderr, format=log_format, level="DEBUG")
    
    # Add file logger if specified
    if log_file:
        logger.add(log_file, format=log_format, level="DEBUG", rotation="10 MB", retention="1 week")

    # Also capture FastAPI logs
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Find caller from where the logged message originated
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
    
    # Intercept all uvicorn and FastAPI logs
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging_logger = logging.getLogger(uvicorn_logger_name)
        logging_logger.handlers = [InterceptHandler()]

# Initialize the log directory
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs"))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "prompt_manager.log")
setup_logging(log_file)

# Log uncaught exceptions
def log_exception(exctype, value, tb):
    """Log uncaught exceptions."""
    logger.opt(exception=True).error(f"Uncaught exception: {value}")
    traceback.print_exception(exctype, value, tb)

sys.excepthook = log_exception

# Create the application
app = FastAPI(
    title="Prompt Management System",
    description="A system for managing AI prompts with composable elements",
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

# Ensure WebSockets can connect
app.add_event_handler("startup", lambda: print("WebSocket endpoints are available"))

# Log startup and request information
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses."""
    start_time = datetime.now()
    
    # Log the request
    logger.debug(f"Request: {request.method} {request.url.path}")
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Log the response
        process_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.debug(f"Response: {request.method} {request.url.path} - Status: {response.status_code} - Took: {process_time:.2f}ms")
        
        return response
    except Exception as e:
        # Log any exceptions
        logger.opt(exception=True).error(f"Error processing request: {request.method} {request.url.path} - {str(e)}")
        raise

# Include API routers
app.include_router(api_router)
app.include_router(session_router)

# Add shutdown endpoint
@app.post("/api/shutdown", tags=["admin"])
async def shutdown_server(request: Request):
    """
    Gracefully shutdown the server.
    """
    from fastapi.responses import JSONResponse
    from fastapi.background import BackgroundTasks
    import asyncio
    import signal
    import os
    
    logger.info("Shutdown request received")
    
    async def shutdown_app():
        # Give a little time for the response to be sent
        await asyncio.sleep(1)
        
        # Send a SIGTERM to the current process
        pid = os.getpid()
        logger.info(f"Sending SIGTERM to process {pid}")
        os.kill(pid, signal.SIGTERM)
    
    # Schedule the shutdown in the background
    background = BackgroundTasks()
    background.add_task(shutdown_app)
    
    # Return a response
    return JSONResponse(
        content={"message": "Server shutdown initiated"},
        background=background
    )

# Set up static files and templates
current_dir = Path(__file__).parent
static_dir = current_dir / "static"
templates_dir = current_dir / "templates"

# Ensure directories exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=templates_dir)


# Main route for the web interface - redirect to the prompt management page
@app.get("/")
async def index(request: Request):
    """Redirect to the prompt management page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/manage/prompts")


# Route for prompt editor
@app.get("/prompts/{prompt_id}")
async def prompt_editor(request: Request, prompt_id: str):
    """Render the prompt editor page."""
    return templates.TemplateResponse(
        "prompt_editor.html", 
        {"request": request, "prompt_id": prompt_id}
    )


# Legacy routes for compatibility - redirect to new routes
@app.get("/fragments/{fragment_id}")
async def fragment_redirect(request: Request, fragment_id: str):
    """Redirect from old fragment route to new prompt route."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/prompts/{fragment_id}")


@app.get("/templates/{template_id}")
async def template_redirect(request: Request, template_id: str):
    """Redirect from old template route to new prompt route."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/prompts/{template_id}")


# Prompt management
@app.get("/manage/prompts")
async def manage_prompts(request: Request):
    """Render the prompt management page."""
    return templates.TemplateResponse("manage_prompts.html", {"request": request})


# Legacy management routes - redirect to unified prompt management
@app.get("/manage/fragments")
async def manage_fragments_redirect(request: Request):
    """Redirect from old fragment management to new prompt management."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/manage/prompts")


@app.get("/manage/templates")
async def manage_templates_redirect(request: Request):
    """Redirect from old template management to new prompt management."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/manage/prompts")


# Settings
@app.get("/settings")
async def settings(request: Request):
    """Render the settings page."""
    return templates.TemplateResponse("settings.html", {"request": request})


def create_default_prompts():
    """Create default prompts if none exist."""
    # Get prompt service
    config_dir = os.path.expanduser("~/.prompt_manager")
    prompts_dir = os.path.join(config_dir, "prompts")
    
    # Ensure directories exist
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Create service
    prompt_service = PromptService([prompts_dir])
    
    # Check if prompts exist
    if len(prompt_service.prompts) == 0:
        # Create default prompts
        default_prompts = [
            {
                "id": "project_overview",
                "content": "# Project Overview\n\nProvide a brief overview of the project here.",
                "description": "Brief project overview",
                "prompt_type": PromptType.STANDARD
            },
            {
                "id": "requirements",
                "content": "# Requirements\n\nList project requirements here.",
                "description": "Project requirements",
                "prompt_type": PromptType.STANDARD
            },
            {
                "id": "maintenance",
                "content": "# Project Maintenance\n\n- Use consistent file naming\n- Write clear comments\n- Update progress reports regularly",
                "description": "Project maintenance guidelines",
                "prompt_type": PromptType.STANDARD
            },
            {
                "id": "initial_tasks",
                "content": "# Initial Tasks\n\nDescribe the first steps to take in the project.",
                "description": "Initial project tasks",
                "prompt_type": PromptType.STANDARD
            },
            {
                "id": "project_start",
                "content": """# Project Start Template

## Project Overview
[[project_overview]]

## Requirements
[[requirements]]

## Project Maintenance
[[maintenance]]

## Initial Tasks
[[initial_tasks]]
""",
                "description": "Template for starting a new project",
                "prompt_type": PromptType.COMPOSITE
            },
            {
                "id": "system_prompt",
                "content": "You are a helpful AI assistant that specializes in helping with project development. You are knowledgeable about software development, project management, and technical writing.",
                "description": "Default system prompt for project assistants",
                "prompt_type": PromptType.SYSTEM
            },
            {
                "id": "user_prompt",
                "content": "I need help with my project. Could you assist me with [TASK]?",
                "description": "Example user prompt",
                "prompt_type": PromptType.USER
            }
        ]
        
        for p in default_prompts:
            # Check if prompt already exists
            if not prompt_service.get_prompt(p["id"]):
                # Create prompt
                prompt_service.create_prompt(
                    id=p["id"],
                    content=p["content"],
                    directory=prompts_dir,
                    prompt_type=p["prompt_type"],
                    description=p["description"],
                    tags=[]
                )


def main(args=None):
    """Run the server."""
    if args is None:
        parser = argparse.ArgumentParser(description="Prompt Management System Server")
        parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
        parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
        parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
        parser.add_argument("--log-file", type=str, default=None, help="Log file path (default: logs/prompt_server.log)")
        parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                            default="DEBUG", help="Log level")
        
        args = parser.parse_args()
    
    # Set up logging
    current_log_file = args.log_file if args.log_file else log_file
    logger.info(f"Starting server with log file: {current_log_file}")
    
    # Create default prompts
    try:
        create_default_prompts()
    except Exception as e:
        logger.opt(exception=True).error(f"Error creating default prompts: {str(e)}")
    
    # Log configuration
    logger.info(f"Starting server on {args.host}:{args.port}")
    if args.reload:
        logger.info("Auto-reload enabled")
    
    # Start the server
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower()
    )


if __name__ == "__main__":
    main()
