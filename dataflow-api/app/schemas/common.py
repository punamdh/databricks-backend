from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class SuccessEnvelope(BaseModel):
    status: str = "success"
    data: Any
    pagination: PaginationMeta | None = None


class ErrorEnvelope(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: dict[str, Any] | None = None


class AuditFields(BaseModel):
    created_by: str = "system"
    updated_by: str = "system"

    model_config = ConfigDict(from_attributes=True)


def success_response(data: Any, pagination: PaginationMeta | None = None) -> dict[str, Any]:
    payload = {"status": "success", "data": data}
    if pagination:
        payload["pagination"] = pagination.model_dump()
    return payload


def raise_api_error(status_code: int, error_code: str, message: str, details: dict[str, Any] | None = None) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"status": "error", "error_code": error_code, "message": message, "details": details or {}},
    )
