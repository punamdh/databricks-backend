from __future__ import annotations

import json

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.orm import PiiAttribute, SchemaVersion, SourceTable, Watermark


class PipelineConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> SourceTable:
        row = SourceTable(**payload)
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, table_config_id: int) -> SourceTable | None:
        return self.db.execute(
            select(SourceTable).where(SourceTable.table_config_id == table_config_id, SourceTable.is_active == 1)
        ).scalar_one_or_none()

    def list(self, page: int, page_size: int, filters: dict):
        conditions = [SourceTable.is_active == filters.get("is_active", 1)]
        if filters.get("env_type"):
            conditions.append(SourceTable.env_type == filters["env_type"])
        if filters.get("connection_source_id"):
            conditions.append(SourceTable.connection_source_id == filters["connection_source_id"])
        if filters.get("config_group"):
            conditions.append(SourceTable.config_group == filters["config_group"])
        if filters.get("load_type"):
            conditions.append(SourceTable.load_type == filters["load_type"])

        base = select(SourceTable).where(and_(*conditions)).order_by(SourceTable.table_config_id.desc())
        total = self.db.execute(select(func.count()).select_from(base.subquery())).scalar_one()
        rows = self.db.execute(base.offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return rows, total

    def upsert_watermark(self, table_config_id: int, payload: dict) -> Watermark:
        row = self.db.execute(
            select(Watermark).where(Watermark.table_config_id == table_config_id, Watermark.is_active == 1)
        ).scalar_one_or_none()
        if row:
            for key, value in payload.items():
                setattr(row, key, value)
            return row
        row = Watermark(table_config_id=table_config_id, **payload)
        self.db.add(row)
        self.db.flush()
        return row

    def get_watermark(self, table_config_id: int) -> Watermark | None:
        return self.db.execute(
            select(Watermark).where(Watermark.table_config_id == table_config_id, Watermark.is_active == 1)
        ).scalar_one_or_none()

    def replace_pii(self, table_config_id: int, env_type: str, actor: str, items: list[dict]) -> list[PiiAttribute]:
        active = self.db.execute(
            select(PiiAttribute).where(PiiAttribute.table_config_id == table_config_id, PiiAttribute.is_active == 1)
        ).scalars().all()
        for row in active:
            row.is_active = 0
            row.updated_by = actor

        created = []
        for item in items:
            row = PiiAttribute(table_config_id=table_config_id, env_type=env_type, created_by=actor, updated_by=actor, **item)
            self.db.add(row)
            created.append(row)
        self.db.flush()
        return created

    def list_pii(self, table_config_id: int) -> list[PiiAttribute]:
        return self.db.execute(
            select(PiiAttribute).where(PiiAttribute.table_config_id == table_config_id, PiiAttribute.is_active == 1)
        ).scalars().all()

    def add_schema_version(self, table_config_id: int, payload: dict) -> SchemaVersion:
        if payload.get("version_number") is None:
            max_version = self.db.execute(
                select(func.max(SchemaVersion.version_number)).where(SchemaVersion.table_config_id == table_config_id)
            ).scalar_one()
            payload["version_number"] = (max_version or 0) + 1
        payload["column_changes_json"] = json.dumps(payload["column_changes_json"])
        row = SchemaVersion(table_config_id=table_config_id, **payload)
        self.db.add(row)
        self.db.flush()
        return row

    def list_schema_versions(self, table_config_id: int) -> list[SchemaVersion]:
        return self.db.execute(
            select(SchemaVersion)
            .where(SchemaVersion.table_config_id == table_config_id, SchemaVersion.is_active == 1)
            .order_by(SchemaVersion.version_number.desc())
        ).scalars().all()
