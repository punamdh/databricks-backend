from app.database.connection import get_spark
from app.database.schema import get_effective_schema

def add_connection_target_id_column():
    spark = get_spark()
    schema = get_effective_schema()
    table_name = f"{schema}.aud_table_run"
    
    try:
        spark.sql(f"ALTER TABLE {table_name} ADD COLUMN connection_target_id BIGINT AFTER connection_source_id")
        print(f"Successfully added connection_target_id column to {table_name}")
    except Exception as e:
        print(f"Error adding column: {e}")
        print("Column may already exist or table may not exist yet")

if __name__ == "__main__":
    add_connection_target_id_column()
