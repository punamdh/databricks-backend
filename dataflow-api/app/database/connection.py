from __future__ import annotations

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

from app.config.settings import get_settings

_spark: SparkSession | None = None


def _databricks_connect_builder() -> SparkSession.Builder:
    settings = get_settings()
    builder = SparkSession.builder.appName(settings.spark_app_name)
    if settings.databricks_host and settings.databricks_token and settings.databricks_cluster_id:
        builder = (
            builder.remote(f"sc://{settings.databricks_host}:443/;token={settings.databricks_token};x-databricks-cluster-id={settings.databricks_cluster_id}")
            .config("spark.databricks.service.port", settings.databricks_port)
        )
    else:
        builder = builder.master(settings.spark_master)
        builder = configure_spark_with_delta_pip(builder)
        builder = (
            builder.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        )
    return builder


def get_spark() -> SparkSession:
    global _spark
    if _spark is None:
        _spark = _databricks_connect_builder().getOrCreate()
        _spark.conf.set("spark.sql.session.timeZone", "UTC")
    return _spark
