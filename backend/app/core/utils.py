import json
import os
from typing import Any, Dict, List

import aiofiles
from app.core.config import settings

SLUG_DB_KEYS = [
    "id",
    "title",
    "slug",
    "url",
    "locale",
    "products",
    "topics",
    "summary",
]


def cleanup_db_output_page(ret: List[Any]) -> Dict[str, Any]:
    """
    Ugly way to compensate for storing arrays in DB as strings (single page)
    """
    result: "Dict[str, Any]" = {}
    rzip = zip(SLUG_DB_KEYS, ret)
    for (k, v) in rzip:
        result[k] = v

    result["summary"] = result["summary"].replace("''", "'")
    result["topics"] = json.loads(result["topics"])
    result["products"] = json.loads(result["products"])
    return result


def cleanup_db_output_overview(ret: List[Any]) -> List[Dict[str, Any]]:
    """
    Ugly way to compensate for storing arrays in DB as strings (overview)
    """
    result: "List[Dict[str, Any]]" = []
    for r in ret:
        result.append({"id": r[0], "title": r[1]})
    return result


async def get_html_content(slug_title: str) -> str:
    try:
        path = os.path.join(settings.HTMLS_PATH, slug_title + ".html")
        async with aiofiles.open(path, mode="r") as f:
            contents = await f.read()
    except Exception as e:
        contents = f"Sorry, could not find file to get contents!"
    return contents
