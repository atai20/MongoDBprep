from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from matcharena.domain.errors import DomainError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_error_handler(_request: Request, exc: PydanticValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": "validation_failed", "message": str(exc)},
        )
