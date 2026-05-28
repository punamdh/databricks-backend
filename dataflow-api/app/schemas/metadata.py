from pydantic import BaseModel


class TableInfo(BaseModel):
    schema_name: str
    table_name: str


class ColumnInfo(BaseModel):
    column_name: str
    data_type: str
    is_nullable: str
    ordinal_position: int
