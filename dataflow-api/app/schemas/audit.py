from pydantic import BaseModel, ConfigDict

class AuditRunCreate(BaseModel):
    created_by: str = "system"
    updated_by: str = "system"
    run_id: str
    table_config_id: int
    connection_source_id: int
    source_attributes: dict | None = None
    target_attributes: dict | None = None
    batch_id: str | None = None
    load_type: str | None = None
    start_time: str
    status: str = "running"
    env_type: str = "dev"


class AuditRunUpdate(BaseModel):
    end_time: str | None = None
    elapsed_seconds: int | None = None
    rows_read: int | None = None
    rows_written: int | None = None
    watermark_start: str | None = None
    watermark_end: str | None = None
    status: str | None = None
    error_message: str | None = None
    error_type: str | None = None
    updated_by: str = "system"


class AuditRunOut(AuditRunCreate):
    table_run_id: int
    end_time: str | None = None
    elapsed_seconds: int | None = None
    rows_read: int | None = None
    rows_written: int | None = None
    watermark_start: str | None = None
    watermark_end: str | None = None
    error_message: str | None = None
    error_type: str | None = None
    is_active: int

    model_config = ConfigDict(from_attributes=True)
