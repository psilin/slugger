import json
from typing import Any, Dict, List

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


def cleanup_db_output(ret: List[Any]) -> List[Dict[str, Any]]:
    """
    Ugly way to compensate for storing arrays in DB as strings
    """
    result: "List[Dict[str, Any]]" = []
    for r in ret:
        rzip = zip(SLUG_DB_KEYS, r)
        res: "Dict[str, Any]" = {}
        for (k, v) in rzip:
            res[k] = v

        res["summary"] = res["summary"].replace("''", "'")
        res["topics"] = json.loads(res["topics"])
        res["products"] = json.loads(res["products"])
        result.append(res)
    return result
