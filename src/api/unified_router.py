"""
Unified API router for prompt management system.
"""

from fastapi import APIRouter
from .router import router as prompts_router

# Create unified router
router = APIRouter()

# Include prompts router
router.include_router(prompts_router)
