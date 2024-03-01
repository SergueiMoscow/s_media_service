"""Main app"""
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from api.views import catalog, storage_manager, storages
from common.exceptions import (
    BaseApiException,
    handle_exception_response,
    handle_validation_error_handler,
)
from common.settings import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

app = FastAPI(docs_url=settings.SWAGGER_URL, redoc_url=settings.REDOC_URL)


origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_exception_handler(BaseApiException, handle_exception_response)
app.add_exception_handler(RequestValidationError, handle_validation_error_handler)

app.include_router(storages.router)
app.include_router(storage_manager.router)
app.include_router(catalog.router)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='localhost', port=8080)
