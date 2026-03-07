"""REST API router -- mounts all route modules at /api/v1."""
from fastapi import APIRouter

from src.api.routes.echo import router as echo_router
from src.api.routes.items import router as items_router
from src.api.routes.easter_egg import router as easter_egg_router
from src.api.routes.docs import router as docs_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(docs_router, tags=["discovery"])
api_router.include_router(echo_router, tags=["echo"])
api_router.include_router(items_router, tags=["items"])
api_router.include_router(easter_egg_router, tags=["easter-egg"])
