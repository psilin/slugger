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
    Adapter for slugs page from DB
    :ret: slugs page in DB format (some arrays stored as strings)
    :returns: page in output format
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
    Adapter for slug from DB
    :ret: slug in DB format (some arrays stored as strings)
    :returns: slug in output format
    """
    result: "List[Dict[str, Any]]" = []
    for r in ret:
        result.append({"id": r[0], "title": r[1]})
    return result


async def get_html_content(slug_title: str) -> str:
    """
    Get HTML file contents from FS using slug title
    :slug_title: name of the slug-related HTML file
    """
    try:
        path = os.path.join(settings.HTMLS_PATH, slug_title + ".html")
        async with aiofiles.open(path, mode="r") as f:
            contents = await f.read()
    except Exception as e:
        contents = f"Sorry, could not find file to get contents!"
    return contents
