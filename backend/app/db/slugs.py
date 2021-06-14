from typing import Any, List

import aiopg
from app.db.errors import EntityDoesNotExist

SQL_SLUG_BU_ID = "SELECT * FROM slugs WHERE id=%s;"
SQL_SLUGS_PAGE = "SELECT id, title FROM slugs ORDER BY id ASC OFFSET %s LIMIT %s;"


async def get_slug_by_id(pool: aiopg.Pool, id: int) -> List[Any]:
    """
    Get slug from DB using connection pool
    :pool: Connection pool
    :id: unique slug id
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as curs:
            # mitigate possible SQL injection
            await curs.execute(SQL_SLUG_BU_ID, (id,))
            ret = []
            async for row in curs:
                ret.append(row)
            if len(ret) == 0:
                raise EntityDoesNotExist
            return ret[0]


async def get_slugs_page(pool: aiopg.Pool, page: int, limit: int) -> List[Any]:
    """
    Get slugs page from DB using connection pool
    :pool: Connection pool
    :page: page number
    :limit: page size
    """
    async with pool.acquire() as conn:
        async with conn.cursor() as curs:
            # mitigate possible SQL injection
            await curs.execute(SQL_SLUGS_PAGE, ((page - 1) * limit, limit))
            ret = []
            async for row in curs:
                ret.append(row)
            if len(ret) == 0:
                raise EntityDoesNotExist
            return ret
