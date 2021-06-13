# from app.api.errors.http_error import http_error_handler
# from app.api.errors.validation_error import http422_error_handler
from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.events import create_start_app_handler, create_stop_app_handler
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME, debug=settings.DEBUG, version=settings.VERSION
    )

    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_stop_app_handler(application))

    # application.add_exception_handler(HTTPException, http_error_handler)
    # application.add_exception_handler(RequestValidationError, http422_error_handler)

    application.include_router(api_router, prefix=settings.API_PREFIX)

    return application


app = get_application()
