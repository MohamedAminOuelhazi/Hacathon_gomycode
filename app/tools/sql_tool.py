from decimal import Decimal

import sqlglot
from sqlalchemy import text
from sqlglot import exp

from app.database.connection import create_database_engine

MAX_ROWS = 500
MAX_SQL_LENGTH = 20_000


def _validate_read_query(sql: str) -> None:
    if not isinstance(sql, str):
        raise ValueError("SQL must be a string.")
    if len(sql) > MAX_SQL_LENGTH:
        raise ValueError(f"SQL query exceeds the {MAX_SQL_LENGTH} character limit.")
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as error:
        raise ValueError(f"SQL could not be parsed: {error}") from error
    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")
    statement = statements[0]
    if not isinstance(statement, exp.Query):
        raise ValueError("Only SELECT queries are allowed.")
    if any(isinstance(node, (exp.DML, exp.DDL)) for node in statement.walk()):
        raise ValueError("Only read-only SELECT queries are allowed.")


def execute_sql(sql: str) -> dict:
    """Execute one PostgreSQL SELECT in a read-only, time-limited transaction."""
    try:
        _validate_read_query(sql)
    except ValueError as error:
        return {"error": str(error), "error_type": "validation_error"}

    engine = create_database_engine()
    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.exec_driver_sql("SET TRANSACTION READ ONLY")
                connection.exec_driver_sql("SET LOCAL statement_timeout = '10s'")
                result = connection.execute(text(sql))
                columns = list(result.keys())
                rows = result.fetchmany(MAX_ROWS + 1)
                truncated = len(rows) > MAX_ROWS
                rows = rows[:MAX_ROWS]
                values = [
                    [_json_value(value) for value in row]
                    for row in rows
                ]
                return {
                    "columns": columns,
                    "rows": values,
                    "row_count": len(values),
                    "truncated": truncated,
                }
    except Exception as error:
        return {"error": str(error), "error_type": type(error).__name__}
    finally:
        engine.dispose()


def _json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
