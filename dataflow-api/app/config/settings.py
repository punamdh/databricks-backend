from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = False

    dbx_schema: str = "dbx_data_platform_poc.ui_metadata"
    spark_app_name: str = "dataflow-api"
    spark_master: str = "local[*]"

    databricks_host: str | None = None
    databricks_token: str | None = None
    databricks_cluster_id: str | None = None
    databricks_port: str = "15001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
