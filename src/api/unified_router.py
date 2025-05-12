"""
Unified API router for prompt management system.
"""

from fastapi import APIRouter
from .router import router as prompts_router
from .fragments_router_redirect import router as fragments_router
from .websocket_routes import router as websocket_router
from .websocket_debug import router as debug_router

# Create unified router
router = APIRouter()

# Include routers
router.include_router(prompts_router)
router.include_router(fragments_router)  # Now using the redirect router
router.include_router(websocket_router)
router.include_router(debug_router)

# For debugging
print(f"API Routes: {[r.path for r in prompts_router.routes]}")
print(f"Fragment Routes (redirected): {[r.path for r in fragments_router.routes]}")
print(f"WebSocket Routes: {[r.path for r in websocket_router.routes]}")
