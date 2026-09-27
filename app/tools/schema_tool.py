from sqlalchemy import inspect

from app.database.connection import create_database_engine


def get_database_schema() -> dict:
    engine = create_database_engine()
    try:
        inspector = inspect(engine)
        tables = {}
        for table_name in inspector.get_table_names():
            tables[table_name] = {
                "columns": {
                    column["name"]: str(column["type"])
                    for column in inspector.get_columns(table_name)
                },
                "relationships": [
                    {
                        "columns": foreign_key["constrained_columns"],
                        "references_table": foreign_key["referred_table"],
                        "references_columns": foreign_key["referred_columns"],
                    }
                    for foreign_key in inspector.get_foreign_keys(table_name)
                ],
            }
        return {"tables": tables}
    finally:
        engine.dispose()
