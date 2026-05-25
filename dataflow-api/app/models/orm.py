from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AuditMixin:
    created_by: Mapped[str] = mapped_column(Text, default="system")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_by: Mapped[str] = mapped_column(Text, default="system")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class ConnMaster(Base, AuditMixin):
    __tablename__ = "conn_master"
    __table_args__ = (UniqueConstraint("connection_name", "env_type", name="uq_connection_name_env"),)

    connection_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_name: Mapped[str] = mapped_column(Text)
    connection_type: Mapped[str] = mapped_column(Text)
    connection_domain_name: Mapped[str] = mapped_column(Text)
    is_target: Mapped[int] = mapped_column(Integer, default=0)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)

    details: Mapped[list["ConnectionDetails"]] = relationship(back_populates="connection")
    auth: Mapped[list["ConnectionAuth"]] = relationship(back_populates="connection")


class ConnectionDetails(Base, AuditMixin):
    __tablename__ = "connection_details"

    connection_details_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("conn_master.connection_id"))
    connection_property_id: Mapped[int] = mapped_column(Integer)
    connection_property: Mapped[str] = mapped_column(Text)
    connection_property_value: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)

    connection: Mapped[ConnMaster] = relationship(back_populates="details")


class ConnectionAuth(Base, AuditMixin):
    __tablename__ = "connection_auth"

    connection_auth_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("conn_master.connection_id"))
    auth_property_id: Mapped[int] = mapped_column(Integer)
    auth_property: Mapped[str] = mapped_column(Text)
    auth_property_value: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)

    connection: Mapped[ConnMaster] = relationship(back_populates="auth")


class SourceTable(Base, AuditMixin):
    __tablename__ = "tbl_source_table"

    table_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connection_source_id: Mapped[int] = mapped_column(ForeignKey("conn_master.connection_id"))
    connection_domain_name: Mapped[str] = mapped_column(Text)
    config_group: Mapped[str] = mapped_column(Text)
    source_attributes: Mapped[str] = mapped_column(Text)
    target_attributes: Mapped[str] = mapped_column(Text)
    load_type: Mapped[str] = mapped_column(Text)
    natural_key_columns: Mapped[str | None] = mapped_column(Text)
    hash_key_column: Mapped[str | None] = mapped_column(Text)
    partition_columns: Mapped[str | None] = mapped_column(Text)
    watermark_enabled: Mapped[int] = mapped_column(Integer, default=0)
    pii_scan_enabled: Mapped[int] = mapped_column(Integer, default=0)
    fail_mode: Mapped[str] = mapped_column(Text, default="halt")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    ingestion_frequency: Mapped[str] = mapped_column(Text, default="adhoc")
    tags: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class Watermark(Base, AuditMixin):
    __tablename__ = "tbl_watermark"

    watermark_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_config_id: Mapped[int] = mapped_column(ForeignKey("tbl_source_table.table_config_id"))
    watermark_column: Mapped[str] = mapped_column(Text)
    watermark_type: Mapped[str] = mapped_column(Text)
    last_value: Mapped[str | None] = mapped_column(Text)
    last_run_id: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class SchemaVersion(Base, AuditMixin):
    __tablename__ = "tbl_schema_version"

    version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_config_id: Mapped[int] = mapped_column(ForeignKey("tbl_source_table.table_config_id"))
    version_number: Mapped[int] = mapped_column(Integer)
    column_count: Mapped[int] = mapped_column(Integer)
    column_changes_json: Mapped[str] = mapped_column(Text)
    change_type: Mapped[str] = mapped_column(Text)
    detected_by_run_id: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class PiiAttribute(Base, AuditMixin):
    __tablename__ = "tbl_pii_attribute"

    pii_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_config_id: Mapped[int] = mapped_column(ForeignKey("tbl_source_table.table_config_id"))
    column_name: Mapped[str] = mapped_column(Text)
    pii_category: Mapped[str] = mapped_column(Text)
    protection_method: Mapped[str] = mapped_column(Text)
    sensitivity: Mapped[str] = mapped_column(Text)
    masking_policy: Mapped[str | None] = mapped_column(Text)
    uc_tag_applied: Mapped[int] = mapped_column(Integer, default=0)
    access_tier: Mapped[str] = mapped_column(Text, default="INTERNAL")
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class AuditTableRun(Base, AuditMixin):
    __tablename__ = "aud_table_run"

    table_run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(Text)
    table_config_id: Mapped[int] = mapped_column(ForeignKey("tbl_source_table.table_config_id"))
    connection_source_id: Mapped[int] = mapped_column(ForeignKey("conn_master.connection_id"))
    source_attributes: Mapped[str | None] = mapped_column(Text)
    target_attributes: Mapped[str | None] = mapped_column(Text)
    batch_id: Mapped[str | None] = mapped_column(Text)
    load_type: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[str] = mapped_column(Text)
    end_time: Mapped[str | None] = mapped_column(Text)
    elapsed_seconds: Mapped[int | None] = mapped_column(Integer)
    rows_read: Mapped[int | None] = mapped_column(Integer)
    rows_written: Mapped[int | None] = mapped_column(Integer)
    watermark_start: Mapped[str | None] = mapped_column(Text)
    watermark_end: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)


class BTSConfig(Base, AuditMixin):
    __tablename__ = "bts_config"

    bts_config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(Text)
    source_config_id: Mapped[int | None] = mapped_column(ForeignKey("tbl_source_table.table_config_id"))
    silver_layout: Mapped[str | None] = mapped_column(Text)
    dq_rules: Mapped[str | None] = mapped_column(Text)
    std_rules: Mapped[str | None] = mapped_column(Text)
    transformation_yaml: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)
    env_type: Mapped[str] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
