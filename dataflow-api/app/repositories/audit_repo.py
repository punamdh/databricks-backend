import json

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.orm import AuditTableRun


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> AuditTableRun:
        for key in ["source_attributes", "target_attributes"]:
            if payload.get(key) is not None and not isinstance(payload[key], str):
                payload[key] = json.dumps(payload[key])
        row = AuditTableRun(**payload)
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, table_run_id: int) -> AuditTableRun | None:
        return self.db.execute(
            select(AuditTableRun).where(AuditTableRun.table_run_id == table_run_id, AuditTableRun.is_active == 1)
        ).scalar_one_or_none()

    def list(self, page: int, page_size: int, run_id: str | None, table_config_id: int | None, status: str | None):
        conditions = [AuditTableRun.is_active == 1]
        if run_id:
            conditions.append(AuditTableRun.run_id == run_id)
        if table_config_id:
            conditions.append(AuditTableRun.table_config_id == table_config_id)
        if status:
            conditions.append(AuditTableRun.status == status)
        q = select(AuditTableRun).where(and_(*conditions)).order_by(AuditTableRun.table_run_id.desc())
        total = self.db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self.db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return rows, total
