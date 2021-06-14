from app.db.slugs import get_slug_by_id, get_slugs_page
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/overview")
async def slugs(request: Request, page: int = 1, limit: int = 20):
    slugs = await get_slugs_page(request.app.state.pool, page, limit)
    return {"result": {"page": page, "limit": limit, "slugs": slugs}}


@router.get("/page/{slug_id}")
async def slug(request: Request, slug_id: int):
    slug = await get_slug_by_id(request.app.state.pool, slug_id)
    return {"slug_id": slug}
