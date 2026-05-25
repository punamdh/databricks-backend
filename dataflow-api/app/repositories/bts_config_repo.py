from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.orm import BTSConfig


class BTSConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> BTSConfig:
        row = BTSConfig(**payload)
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, bts_config_id: int) -> BTSConfig | None:
        return self.db.execute(
            select(BTSConfig).where(BTSConfig.bts_config_id == bts_config_id, BTSConfig.is_active == 1)
        ).scalar_one_or_none()

    def list(self, page: int, page_size: int, env_type: str | None, dataset_name: str | None):
        conditions = [BTSConfig.is_active == 1]
        if env_type:
            conditions.append(BTSConfig.env_type == env_type)
        if dataset_name:
            conditions.append(BTSConfig.dataset_name.ilike(f"%{dataset_name}%"))
        q = select(BTSConfig).where(and_(*conditions)).order_by(BTSConfig.bts_config_id.desc())
        total = self.db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
        rows = self.db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return rows, total
