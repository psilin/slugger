from app.api.api_v1.endpoints import slugs
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(slugs.router, tags=["slugs"])
