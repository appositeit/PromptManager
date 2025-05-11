"""
API routes for fragment management - redirected to prompts.

This module provides a compatibility layer that redirects fragment API calls
to the prompt API.
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from starlette.routing import NoMatchFound

# Create router with the same prefix as the original fragments router
router = APIRouter(prefix="/api/prompts/fragments", tags=["fragments"], include_in_schema=False)

# Redirect all fragment routes to prompt routes
@router.get("/{path:path}", include_in_schema=False)
async def redirect_to_prompts(request: Request, path: str):
    """Redirect fragment paths to prompt paths."""
    new_path = request.url.path.replace("/api/prompts/fragments", "/api/prompts")
    return RedirectResponse(url=new_path)

@router.post("/{path:path}", include_in_schema=False)
async def redirect_post_to_prompts(request: Request, path: str):
    """Redirect fragment paths to prompt paths."""
    new_path = request.url.path.replace("/api/prompts/fragments", "/api/prompts")
    return RedirectResponse(url=new_path, status_code=307)  # 307 preserves the HTTP method

@router.put("/{path:path}", include_in_schema=False)
async def redirect_put_to_prompts(request: Request, path: str):
    """Redirect fragment paths to prompt paths."""
    new_path = request.url.path.replace("/api/prompts/fragments", "/api/prompts")
    return RedirectResponse(url=new_path, status_code=307)  # 307 preserves the HTTP method

@router.delete("/{path:path}", include_in_schema=False)
async def redirect_delete_to_prompts(request: Request, path: str):
    """Redirect fragment paths to prompt paths."""
    new_path = request.url.path.replace("/api/prompts/fragments", "/api/prompts")
    return RedirectResponse(url=new_path, status_code=307)  # 307 preserves the HTTP method

# Special case for /api/prompts/fragments/expand
@router.post("/expand", include_in_schema=False)
async def redirect_expand_to_prompts(request: Request):
    """Redirect expand endpoint to prompts expand endpoint."""
    return RedirectResponse(url="/api/prompts/expand", status_code=307)
