import asyncio
import logging

import aiopg
from app.core.config import settings
from fastapi import FastAPI


async def connect_to_db(app: FastAPI) -> None:
    logging.info(f"Connecting to {settings.DATABASE_DSN}")

    app.state.pool = await aiopg.create_pool(settings.DATABASE_DSN)

    logging.info("Connection established")


async def close_db_connection(app: FastAPI) -> None:
    logging.info("Closing connection to database")

    await app.state.pool.close()

    logging.info("Connection closed")
