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
    mask_pattern: str | None = None
    key_scope: str | None = None
    key_name: str | None = None
    hash_algorithm: str | None = None
    uc_tag_applied: bool = False
    uc_tag_key: str | None = None
    uc_tag_value: str | None = None
    access_tier: str = "INTERNAL"
    allowed_groups: str | None = None


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
    table_group_id: int | None = None
    source_attributes: dict
    target_attributes: dict
    load_type: str
    natural_key_columns: str | None = None
    hash_key_column: str | None = None
    partition_columns: str | None = None
    watermark_enabled: bool = False
    pii_scan_enabled: bool = False
    ingestion_frequency: str = "adhoc"
    tags: list[str] = Field(default_factory=list)
    env_type: str = "dev"


class PipelineConfigCreate(PipelineConfigBase):
    created_by: str = "system"
    updated_by: str = "system"
    watermark: WatermarkPayload | None = None


class PipelineConfigUpdate(BaseModel):
    connection_source_id: int | None = None
    connection_domain_name: str | None = None
    table_group_id: int | None = None
    source_attributes: dict | None = None
    target_attributes: dict | None = None
    load_type: str | None = None
    natural_key_columns: str | None = None
    hash_key_column: str | None = None
    partition_columns: str | None = None
    watermark_enabled: bool | None = None
    pii_scan_enabled: bool | None = None
    ingestion_frequency: str | None = None
    tags: list[str] | None = None
    env_type: str | None = None
    updated_by: str = "system"


class PipelineConfigOut(PipelineConfigBase):
    table_config_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
