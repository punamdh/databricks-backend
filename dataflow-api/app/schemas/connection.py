from pydantic import BaseModel, ConfigDict, Field

class ConnectionBase(BaseModel):
    connection_name: str
    connection_type: str
    connection_domain_name: str
    is_target: int = 0
    env_type: str = "dev"


class ConnectionCreate(ConnectionBase):
    created_by: str = "system"
    updated_by: str = "system"
    auth_type: str = "none"
    details: dict[str, str] = Field(default_factory=dict)
    auth: dict[str, str] = Field(default_factory=dict)


class ConnectionUpdate(BaseModel):
    connection_domain_name: str | None = None
    is_target: int | None = None
    details: dict[str, str] | None = None
    auth_type: str | None = None
    auth: dict[str, str] | None = None
    updated_by: str = "system"


class ConnectionOut(ConnectionBase):
    connection_id: int
    is_active: int
    details: dict[str, str] = Field(default_factory=dict)
    auth: dict[str, str] = Field(default_factory=dict)
    auth_type: str | None = None

    model_config = ConfigDict(from_attributes=True)
