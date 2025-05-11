"""
Unified API router for prompt management system.
"""

from fastapi import APIRouter
from .router import router as prompts_router
from .fragments_router import router as fragments_router
from .websocket_routes import router as websocket_router

# Create unified router
router = APIRouter()

# Include routers
router.include_router(prompts_router)
router.include_router(fragments_router)
router.include_router(websocket_router)
