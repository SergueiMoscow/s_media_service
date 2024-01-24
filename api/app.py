"""Main app"""
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from api.views import storages
from common.exceptions import (
    BaseApiException,
    handle_exception_response,
    handle_validation_error_handler,
)

logger = logging.getLogger(__name__)

app = FastAPI(docs_url='/')

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

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='localhost', port=8000)
