import logging

import aiopg
from app.core.config import settings
from fastapi import FastAPI


async def connect_to_db(app: FastAPI) -> None:
    logger = logging.getLogger("uvicorn.asgi")
    logger.info(f"Connecting to {settings.DATABASE_DSN}")

    app.state.pool = await aiopg.create_pool(settings.DATABASE_DSN)

    logger.info("Connection established")


async def close_db_connection(app: FastAPI) -> None:
    logger = logging.getLogger("uvicorn.asgi")
    logger.info("Closing connection to database")

    await app.state.pool.close()

    logger.info("Connection closed")
