from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
async def slugs():
    return {"result": "overview"}


@router.get("/page/{slug_id}")
async def slug(slug_id: int):
    return {"slug_id": slug_id}
