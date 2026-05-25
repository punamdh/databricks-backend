from pydantic import BaseModel, ConfigDict, Field

class BTSConfigCreate(BaseModel):
    created_by: str = "system"
    updated_by: str = "system"
    dataset_name: str
    source_config_id: int | None = None
    silver_layout: list[dict] = Field(default_factory=list)
    dq_rules: list[dict] = Field(default_factory=list)
    std_rules: list[dict] = Field(default_factory=list)
    transformation_yaml: str | None = None
    tags: list[str] = Field(default_factory=list)
    env_type: str = "dev"


class BTSConfigUpdate(BaseModel):
    dataset_name: str | None = None
    source_config_id: int | None = None
    silver_layout: list[dict] | None = None
    dq_rules: list[dict] | None = None
    std_rules: list[dict] | None = None
    transformation_yaml: str | None = None
    tags: list[str] | None = None
    updated_by: str = "system"


class BTSConfigOut(BTSConfigCreate):
    bts_config_id: int
    is_active: int

    model_config = ConfigDict(from_attributes=True)
