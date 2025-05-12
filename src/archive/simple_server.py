"""
Simple server for the prompt manager.

This is a simpler version of the server that helps debug import issues.
"""

import os
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Create app
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

# Get the base path
BASE_DIR = Path(__file__).resolve().parent

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Set up templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Import routers
from src.api.router import router as prompts_router
from src.api.fragments_router import router as fragments_router

# Include routers
app.include_router(prompts_router)
app.include_router(fragments_router)

# Add a simple root route
@app.get("/")
async def root():
    return {"message": "Welcome to Prompt Manager API"}

# The app is defined above, no action needed in this block
