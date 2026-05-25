from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.orm import ConnMaster, ConnectionAuth, ConnectionDetails


class ConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_master(self, payload: dict) -> ConnMaster:
        record = ConnMaster(**payload)
        self.db.add(record)
        self.db.flush()
        return record

    def add_details(self, connection_id: int, env_type: str, details: dict[str, str], actor: str) -> None:
        for idx, (key, value) in enumerate(details.items(), start=1):
            self.db.add(
                ConnectionDetails(
                    connection_id=connection_id,
                    connection_property_id=idx,
                    connection_property=key,
                    connection_property_value=str(value),
                    env_type=env_type,
                    created_by=actor,
                    updated_by=actor,
                )
            )

    def add_auth(self, connection_id: int, env_type: str, auth: dict[str, str], actor: str) -> None:
        for idx, (key, value) in enumerate(auth.items(), start=1):
            self.db.add(
                ConnectionAuth(
                    connection_id=connection_id,
                    auth_property_id=idx,
                    auth_property=key,
                    auth_property_value=str(value),
                    env_type=env_type,
                    created_by=actor,
                    updated_by=actor,
                )
            )

    def find_duplicate(self, connection_name: str, env_type: str, exclude_id: int | None = None) -> bool:
        query = select(ConnMaster).where(
            ConnMaster.connection_name == connection_name,
            ConnMaster.env_type == env_type,
        )
        if exclude_id:
            query = query.where(ConnMaster.connection_id != exclude_id)
        return self.db.execute(query).scalar_one_or_none() is not None

    def list_connections(self, page: int, page_size: int, filters: dict, search: str | None):
        conditions = [ConnMaster.is_active == filters.get("is_active", 1)]
        if filters.get("env_type"):
            conditions.append(ConnMaster.env_type == filters["env_type"])
        if filters.get("connection_type"):
            conditions.append(ConnMaster.connection_type == filters["connection_type"])
        if filters.get("is_target") is not None:
            conditions.append(ConnMaster.is_target == filters["is_target"])
        if search:
            conditions.append(
                or_(
                    ConnMaster.connection_name.ilike(f"%{search}%"),
                    ConnMaster.connection_domain_name.ilike(f"%{search}%"),
                )
            )

        base_query = select(ConnMaster).where(and_(*conditions)).order_by(ConnMaster.connection_id.desc())
        total = self.db.execute(select(func.count()).select_from(base_query.subquery())).scalar_one()
        rows = self.db.execute(base_query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return rows, total

    def get_connection(self, connection_id: int) -> ConnMaster | None:
        return self.db.execute(
            select(ConnMaster).where(ConnMaster.connection_id == connection_id, ConnMaster.is_active == 1)
        ).scalar_one_or_none()

    def get_details_dict(self, connection_id: int) -> dict[str, str]:
        rows = self.db.execute(
            select(ConnectionDetails).where(ConnectionDetails.connection_id == connection_id, ConnectionDetails.is_active == 1)
        ).scalars().all()
        return {row.connection_property: row.connection_property_value or "" for row in rows}

    def get_auth_dict(self, connection_id: int) -> dict[str, str]:
        rows = self.db.execute(
            select(ConnectionAuth).where(ConnectionAuth.connection_id == connection_id, ConnectionAuth.is_active == 1)
        ).scalars().all()
        return {row.auth_property: row.auth_property_value or "" for row in rows}
