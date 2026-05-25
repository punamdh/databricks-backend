from pydantic import BaseModel, ConfigDict, Field

class WatermarkPayload(BaseModel):
    watermark_column: str
    watermark_type: str
    last_value: str | None = None
    last_run_id: str | None = None
    env_type: str = "dev"
    updated_by: str = "system"


class PiiPayload(BaseModel):
    column_name: str
    pii_category: str
    protection_method: str
    sensitivity: str
    masking_policy: str | None = None
    uc_tag_applied: int = 0
    access_tier: str = "INTERNAL"


class SchemaVersionPayload(BaseModel):
    version_number: int | None = None
    column_count: int
    column_changes_json: dict
    change_type: str
    detected_by_run_id: str | None = None
    env_type: str = "dev"
    created_by: str = "system"


class PipelineConfigBase(BaseModel):
    connection_source_id: int
    connection_domain_name: str
    config_group: str
    source_attributes: dict
    target_attributes: dict
    load_type: str
    natural_key_columns: str | None = None
    hash_key_column: str | None = None
    partition_columns: str | None = None
    watermark_enabled: int = 0
    pii_scan_enabled: int = 0
    fail_mode: str = "halt"
    retry_count: int = 0
    ingestion_frequency: str = "adhoc"
    tags: list[str] = Field(default_factory=list)
    env_type: str = "dev"


class PipelineConfigCreate(PipelineConfigBase):
    created_by: str = "system"
    updated_by: str = "system"
    watermark: WatermarkPayload | None = None


class PipelineConfigUpdate(BaseModel):
    source_attributes: dict | None = None
    target_attributes: dict | None = None
    load_type: str | None = None
    natural_key_columns: str | None = None
    hash_key_column: str | None = None
    partition_columns: str | None = None
    watermark_enabled: int | None = None
    pii_scan_enabled: int | None = None
    fail_mode: str | None = None
    retry_count: int | None = None
    ingestion_frequency: str | None = None
    tags: list[str] | None = None
    updated_by: str = "system"


class PipelineConfigOut(PipelineConfigBase):
    table_config_id: int
    is_active: int

    model_config = ConfigDict(from_attributes=True)
