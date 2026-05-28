from pydantic import BaseModel, Field

from app.schemas.pipeline_config import PiiPayload, WatermarkPayload


class STBConfigGroupCreate(BaseModel):
    connection_domain_name: str
    source_attributes: dict
    target_attributes: dict
    load_type: str
    natural_key_columns: str | None = None
    hash_key_column: str | None = None
    partition_columns: str | None = None
    watermark_enabled: bool = False
    pii_scan_enabled: bool = False
    ingestion_frequency: str = "adhoc"
    env_type: str = "dev"
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)
    watermark: WatermarkPayload | None = None
    pii_columns: list[PiiPayload] = Field(default_factory=list)


class STBConfigCreate(BaseModel):
    description: str | None = None
    connection_source_id: int
    created_by: str = "system"
    updated_by: str = "system"
    config_groups: list[STBConfigGroupCreate] = Field(min_length=1)
