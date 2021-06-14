import aiopg

SQL_SLUG_BU_ID = "SELECT * FROM slugs WHERE id=%s;"
SQL_SLUGS_PAGE = "SELECT * FROM slugs ORDER BY id ASC OFFSET %s LIMIT %s;"


async def get_slug_by_id(pool: aiopg.Pool, id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as curs:
            # mitigate possible SQL injection
            await curs.execute(SQL_SLUG_BU_ID, (id,))
            ret = []
            async for row in curs:
                ret.append(row)
            return ret


async def get_slugs_page(pool: aiopg.Pool, page: int, limit: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as curs:
            # mitigate possible SQL injection
            await curs.execute(SQL_SLUGS_PAGE, ((page - 1) * limit, limit))
            ret = []
            async for row in curs:
                ret.append(row)
            return ret
