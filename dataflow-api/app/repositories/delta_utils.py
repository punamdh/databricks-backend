from __future__ import annotations

import re
from datetime import datetime, timezone

from pyspark.sql import DataFrame, Row
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from app.database.connection import get_spark
from app.database.schema import get_effective_schema

__all__ = ['now_utc_iso', 'now_utc', 'row_to_dict', 'table_name', 'next_id', 'append_rows', 'paginate', 'update_rows', 'bool_value']


def bool_value(table_name: str, column_name: str, value: bool):
    """
    Return the appropriate value for a boolean comparison based on the column's actual type.
    If column is stored as BIGINT/INT, returns 1/0. If BOOLEAN, returns True/False.
    
    Args:
        table_name: Full table name
        column_name: Column name to check
        value: Boolean value to convert
    
    Returns:
        1/0 for integer columns, True/False for boolean columns
    """
    spark = get_spark()
    try:
        table_df = spark.table(table_name)
        schema = table_df.schema
        for field in schema.fields:
            if field.name == column_name:
                col_type = field.dataType.typeName().lower()
                if "int" in col_type or "long" in col_type or "bigint" in col_type:
                    return 1 if value else 0
                else:
                    return value
    except Exception:
        pass
    # Default to boolean value
    return value


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def row_to_dict(row: Row) -> dict:
    """Safely convert a Row to dict, handling NULL values properly."""
    return row.asDict()


def table_name(name: str) -> str:
    schema = get_effective_schema()
    # For Unity Catalog (catalog.schema format), don't use backticks around schema
    # For simple schema names, use backticks
    if "." in schema:
        return f"{schema}.{name}"
    else:
        return f"`{schema}`.{name}"


def next_id(table: str, id_column: str) -> int:
    spark = get_spark()
    result = spark.table(table).agg(F.max(F.col(id_column)).alias("max_id")).collect()[0]
    result_dict = result.asDict()
    max_id = result_dict.get("max_id")
    return int(max_id) + 1 if max_id is not None else 1


def append_rows(table: str, rows: list[dict]) -> None:
    if not rows:
        return
    spark = get_spark()
    table_df = spark.table(table)
    schema = table_df.schema
    
    # Check for identity columns by examining table properties and metadata
    # Identity columns may have various metadata indicators or be in table properties
    identity_columns = set()
    
    # Method 1: Try to get table properties to check for identity columns
    try:
        table_props = spark.sql(f"DESCRIBE TABLE EXTENDED {table}").collect()
        for row in table_props:
            row_dict = row.asDict()
            col_name = row_dict.get("col_name", "")
            data_type = row_dict.get("data_type", "")
            comment = str(row_dict.get("comment", ""))
            
            # Check if it's marked as IDENTITY or GENERATED in data_type or comment
            data_type_upper = str(data_type).upper()
            comment_upper = comment.upper()
            
            if ("IDENTITY" in data_type_upper or 
                "GENERATED" in data_type_upper or
                "IDENTITY" in comment_upper or
                "GENERATED ALWAYS AS IDENTITY" in comment_upper):
                identity_columns.add(col_name)
    except Exception:
        pass
    
    # Method 2: Check field metadata
    for field in schema.fields:
        if field.metadata:
            # Check various possible metadata keys for identity columns
            metadata_str = str(field.metadata).upper()
            if (field.metadata.get("__IDENTITY_INFO__") or 
                field.metadata.get("IDENTITY_INFO") or
                field.metadata.get("IS_IDENTITY") or
                field.metadata.get("CURRENT_DEFAULT") == "GENERATED_ALWAYS_AS_IDENTITY" or
                "IDENTITY" in metadata_str or
                "GENERATED_ALWAYS_AS_IDENTITY" in metadata_str):
                identity_columns.add(field.name)
    
    # Method 3: Try to detect by checking if column values are being explicitly provided
    # but the column has auto-increment behavior - use SHOW CREATE TABLE
    try:
        create_stmt = spark.sql(f"SHOW CREATE TABLE {table}").collect()[0]["createtab_stmt"]
        # Match patterns like "column_name BIGINT GENERATED ALWAYS AS IDENTITY"
        identity_pattern = re.compile(r'(\w+)\s+\w+\s+GENERATED\s+ALWAYS\s+AS\s+IDENTITY', re.IGNORECASE)
        matches = identity_pattern.findall(create_stmt)
        for match in matches:
            identity_columns.add(match)
    except Exception:
        pass
    
    # Method 4: Fallback - check if any column in schema is NOT present in any of the input rows
    # These are likely auto-generated columns (identity, default, etc.)
    if rows:
        first_row_keys = set(rows[0].keys())
        for field in schema.fields:
            if field.name not in first_row_keys:
                # This column is not provided in input, likely auto-generated
                identity_columns.add(field.name)
    
    # Convert boolean fields to match schema expectations
    from pyspark.sql.types import BooleanType, TimestampType, StringType
    import pandas as pd
    
    # Get non-identity field names
    non_identity_fields = [f for f in schema.fields if f.name not in identity_columns]
    
    # Convert rows to ensure proper types - only include non-identity columns
    converted_rows = []
    for row in rows:
        converted_row = {}
        
        for field in non_identity_fields:
            field_name = field.name
            value = row.get(field_name)
            
            # Handle type conversions
            if value is not None:
                if isinstance(field.dataType, BooleanType) and isinstance(value, int):
                    converted_row[field_name] = bool(value)
                elif isinstance(field.dataType, TimestampType) and isinstance(value, str):
                    # Keep as string, Spark will handle conversion
                    converted_row[field_name] = value
                else:
                    converted_row[field_name] = value
            else:
                # Use None for nullable fields
                converted_row[field_name] = None
        
        converted_rows.append(converted_row)
    
    # Use pandas DataFrame as intermediate to handle nulls better
    pdf = pd.DataFrame(converted_rows)
    
    # Ensure all columns exist (in case some rows are missing certain columns)
    for field in non_identity_fields:
        if field.name not in pdf.columns:
            pdf[field.name] = None
    
    # Reorder columns to match schema and ensure only non-identity columns are present
    pdf = pdf[[f.name for f in non_identity_fields]]
    
    # Create Spark DataFrame from pandas with only non-identity fields
    # Make all fields nullable to avoid casting errors with None values
    from pyspark.sql.types import StructType, StructField
    nullable_fields = [
        StructField(f.name, f.dataType, nullable=True, metadata=f.metadata)
        for f in non_identity_fields
    ]
    insert_schema = StructType(nullable_fields)
    df = spark.createDataFrame(pdf, schema=insert_schema)
    
    df.write.format("delta").mode("append").saveAsTable(table)


def update_rows(table: str, condition: str, updates: dict) -> None:
    """
    Update rows in a Delta table using SQL UPDATE for Spark Connect compatibility.
    
    Args:
        table: Full table name (e.g., 'schema.table_name')
        condition: WHERE condition as SQL string (e.g., 'connection_id = 123 AND is_active = TRUE')
        updates: Dictionary of column names to new values (e.g., {'updated_by': 'user', 'updated_at': '2024-01-01'})
    """
    if not updates:
        print("Warning: update_rows called with empty updates dict")
        return
        
    spark = get_spark()
    
    # Get table schema to determine column types
    table_df = spark.table(table)
    schema = table_df.schema
    column_types = {field.name: field.dataType.typeName() for field in schema.fields}
    
    # Build SET clause for SQL UPDATE
    set_clauses = []
    for col, val in updates.items():
        # Handle different types of values
        if val is None:
            set_clauses.append(f"{col} = NULL")
        elif isinstance(val, bool):
            # Check if the column is stored as integer/bigint, convert bool to 0/1
            col_type = column_types.get(col, "").lower()
            if "int" in col_type or "long" in col_type or "bigint" in col_type:
                set_clauses.append(f"{col} = {1 if val else 0}")
            else:
                set_clauses.append(f"{col} = {str(val).upper()}")
        elif isinstance(val, (int, float)):
            set_clauses.append(f"{col} = {val}")
        else:
            # String values need to be escaped and quoted
            escaped_val = str(val).replace("'", "''")
            set_clauses.append(f"{col} = '{escaped_val}'")
    
    set_clause = ", ".join(set_clauses)
    
    # Fix boolean values in WHERE condition (replace TRUE/FALSE with 1/0 for BIGINT columns)
    fixed_condition = condition
    for field in schema.fields:
        col_type = field.dataType.typeName().lower()
        if "int" in col_type or "long" in col_type or "bigint" in col_type:
            # Replace column = TRUE with column = 1
            fixed_condition = fixed_condition.replace(f"{field.name} = TRUE", f"{field.name} = 1")
            fixed_condition = fixed_condition.replace(f"{field.name} = true", f"{field.name} = 1")
            # Replace column = FALSE with column = 0
            fixed_condition = fixed_condition.replace(f"{field.name} = FALSE", f"{field.name} = 0")
            fixed_condition = fixed_condition.replace(f"{field.name} = false", f"{field.name} = 0")
    
    # Execute UPDATE using SQL
    update_sql = f"UPDATE {table} SET {set_clause} WHERE {fixed_condition}"
    
    # DEBUG: Print the SQL being executed
    print(f"[DEBUG] Executing UPDATE SQL: {update_sql}")
    
    try:
        result = spark.sql(update_sql)
        print(f"[DEBUG] UPDATE executed successfully")
        # Try to show result if available
        try:
            result.show()
        except:
            pass
    except Exception as e:
        print(f"[ERROR] UPDATE failed: {e}")
        raise


def paginate(df: DataFrame, page: int, page_size: int, order_col: str):
    total = df.count()
    start = (page - 1) * page_size
    end = start + page_size
    window = Window.orderBy(F.col(order_col).desc())
    paged = (
        df.withColumn("__row_num", F.row_number().over(window))
        .filter((F.col("__row_num") > start) & (F.col("__row_num") <= end))
        .drop("__row_num")
    )
    return [row_to_dict(row) for row in paged.collect()], total
