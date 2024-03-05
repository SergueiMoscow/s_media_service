from enum import Enum

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

ERROR_CODE = 'error_code'
ERROR_MESSAGE = 'error_message'


class BaseErrorMessage(dict, Enum):
    @property
    def error_code(self) -> str:
        return self.value[ERROR_CODE]

    @property
    def error_message(self) -> str:
        return self.value[ERROR_MESSAGE]


class BaseApiException(Exception):
    status_code: int

    def __init__(
        self,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ):
        self.error_code = error_code
        self.error_message = error_message

    async def get_response_data(self):
        return JSONResponse(
            content={
                'error': {
                    'error_code': self.error_code,
                    'error_message': self.error_message,
                },
            },
            status_code=self.status_code,
        )


class HTTPErrorMessage(BaseErrorMessage):
    INCORRECT_DATA = {
        ERROR_CODE: 'incorrect_data',
        ERROR_MESSAGE: 'Некорректные данные: {verbose_errors}.',
    }


class BadRequest(BaseApiException):
    status_code = status.HTTP_400_BAD_REQUEST


class InternalServerError(BaseApiException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class NotFound(BaseApiException):
    status_code = status.HTTP_404_NOT_FOUND


class NotAllowed(BaseApiException):
    status_code = status.HTTP_401_UNAUTHORIZED


async def handle_exception_response(
    request: Request, exc: BaseApiException  # pylint: disable=unused-argument
) -> JSONResponse:  # pylint: disable=unused-argument
    return await exc.get_response_data()


async def handle_validation_error_handler(
    request: Request,  # pylint: disable=unused-argument
    exc: RequestValidationError,
) -> JSONResponse:  # pylint: disable=unused-argument
    param_name_index = -1
    all_errors = exc.errors()
    verbose_errors = ', '.join(
        [param_name for param_name in error['loc'] if isinstance(param_name, str)][param_name_index]
        + ' '
        + error['msg']
        for error in all_errors
    )
    error = await BadRequest(
        error_code='incorrect_data',
        error_message=verbose_errors,
    ).get_response_data()

    return error


class InvalidKey(BadRequest):
    def __init__(self):
        self.error_code = 'invalid_key'
        self.error_message = 'Неверный ключ сервиса'
