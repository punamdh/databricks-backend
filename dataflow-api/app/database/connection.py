from __future__ import annotations

import time
import logging
from pyspark.sql import SparkSession
from pyspark.errors.exceptions.connect import SparkConnectGrpcException
from delta import configure_spark_with_delta_pip

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_spark: SparkSession | None = None


def _databricks_connect_builder() -> SparkSession.Builder:
    settings = get_settings()
    builder = SparkSession.builder.appName(settings.spark_app_name)
    if settings.databricks_host and settings.databricks_token and settings.databricks_cluster_id:
        # Extract hostname without protocol and trailing slash
        host = settings.databricks_host.replace("https://", "").replace("http://", "").rstrip("/")
        builder = (
            builder.remote(f"sc://{host}:443/;token={settings.databricks_token};x-databricks-cluster-id={settings.databricks_cluster_id};user_id=token")
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
        max_retries = 5
        retry_delay = 10  # seconds
        
        for attempt in range(max_retries):
            try:
                _spark = _databricks_connect_builder().getOrCreate()
                _spark.conf.set("spark.sql.session.timeZone", "UTC")
                logger.info("Successfully connected to Spark cluster")
                break
            except SparkConnectGrpcException as e:
                if "state=PENDING" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Cluster is starting up (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
    return _spark
