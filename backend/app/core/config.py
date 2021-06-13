from pydantic import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api/v1"
    VERSION: str = "0.1.0"
    PROJECT_NAME: str = "FastAPI Slugger"
    DEBUG: bool = True
    DATABASE_DSN: str = "host=localhost dbname=postgres user=postgres password=postgres"


settings = Settings()
