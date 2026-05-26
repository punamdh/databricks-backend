from app.config.settings import get_settings


def get_effective_schema() -> str:
    settings = get_settings()
    if settings.databricks_host and settings.databricks_token and settings.databricks_cluster_id:
        return settings.dbx_schema
    return settings.dbx_schema.replace(".", "_")
