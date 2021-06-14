from typing import Callable

from app.db.events import close_db_connection, connect_to_db
from fastapi import FastAPI


def create_start_app_handler(app: FastAPI) -> Callable:
    """
    Startup handler factory
    :app: application
    :returns: startup handler (opens DB connection)
    """

    async def start_app() -> None:
        await connect_to_db(app)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """
    Shutdown handler factory
    :app: application
    :returns: shutdown handler (closes DB connection)
    """

    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app
