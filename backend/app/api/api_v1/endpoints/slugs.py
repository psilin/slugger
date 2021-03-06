from app.core import utils
from app.db.errors import EntityDoesNotExist
from app.db.slugs import get_slug_by_id, get_slugs_page
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse

router = APIRouter()


@router.get("/overview")
async def slugs(request: Request, page: int = 1, limit: int = 20) -> None:
    """
    Request handler (slugs page)
    :request: HTTP request
    :page: page number
    :limit: page size
    """
    if page < 1:
        raise HTTPException(
            status_code=422, detail="Page query parameter should be >= 1."
        )
    elif limit < 1:
        raise HTTPException(
            status_code=422, detail="Limit query parameter should be >= 1."
        )
    try:
        slugs = await get_slugs_page(request.app.state.pool, page, limit)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="No such entity.")
    result = utils.cleanup_db_output_overview(slugs)
    return JSONResponse({"page": page, "limit": limit, "slugs": result})


@router.get("/page/{slug_id}")
async def slug(request: Request, slug_id: int) -> None:
    """
    Request handler (unique slug)
    :request: HTTP request
    :id: unique slug id
    """
    try:
        slug = await get_slug_by_id(request.app.state.pool, slug_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="No such entity.")
    result = utils.cleanup_db_output_page(slug)
    result["html"] = await utils.get_html_content(result["slug"])
    return JSONResponse(result)
