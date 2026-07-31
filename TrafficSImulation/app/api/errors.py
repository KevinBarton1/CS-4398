import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.models import ErrorResponse, ValidationField
from app.map.errors import (
    DomainError,
    InvalidLocationError,
    MapsNotConfiguredError,
    NoRouteFoundError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

logger = logging.getLogger(__name__)


class SameOriginDestinationError(DomainError):
    code = "same_origin_destination"
    status = 400

    def __init__(self) -> None:
        super().__init__(
            "Origin and destination resolved to the same place. "
            "Choose two different locations."
        )


async def domain_exception_handler(
    request: Request,
    error: DomainError,
) -> JSONResponse:
    logger.log(
        logging.INFO if error.status < 500 else logging.WARNING,
        "Request failed: code=%s status=%s endpoint=%s %s",
        error.code,
        error.status,
        request.method,
        request.url.path,
    )
    body = ErrorResponse(detail=error.detail, code=error.code)
    return JSONResponse(
        status_code=error.status,
        content=body.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    fields = [
        ValidationField(
            field=".".join(
                str(part) for part in item["loc"] if part != "body"
            ),
            message=item["msg"],
        )
        for item in error.errors()
    ]
    logger.info(
        "Request failed: code=validation_error status=422 endpoint=%s %s",
        request.method,
        request.url.path,
    )
    body = ErrorResponse(
        detail="Request validation failed.",
        code="validation_error",
        fields=fields,
    )
    return JSONResponse(status_code=422, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )


__all__ = [
    "DomainError",
    "InvalidLocationError",
    "MapsNotConfiguredError",
    "NoRouteFoundError",
    "SameOriginDestinationError",
    "UpstreamTimeoutError",
    "UpstreamUnavailableError",
    "domain_exception_handler",
    "register_exception_handlers",
    "validation_exception_handler",
]
