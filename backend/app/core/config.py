import logging

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api/v1"
    VERSION: str = "0.1.0"
    PROJECT_NAME: str = "FastAPI Slugger"
    DEBUG: bool = True
    DATABASE_DSN: str = (
        "host=postgres port=5432 dbname=postgres user=postgres password=postgres"
    )
    HTMLS_PATH: str = "/opt/htmls"


settings = Settings()

# logging config
LOGGING_LEVEL = logging.DEBUG if settings.DEBUG else logging.INFO
LOGGERS = ("uvicorn.asgi", "uvicorn.access", "uvicorn.error")
for logger_name in LOGGERS:
    logger = logging.getLogger(logger_name)
    logger.setLevel(LOGGING_LEVEL)
