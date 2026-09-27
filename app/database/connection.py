import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()


def _normalize_database_url(value: str) -> str:
    value = value.strip()
    while value.startswith("DATABASE_URL="):
        value = value[len("DATABASE_URL="):].strip()
    return value


def get_database_url() -> str:
    return _normalize_database_url(
        os.getenv("DATABASE_URL", "postgresql+psycopg://soufet:oma@localhost:5432/soufet")
    )


def create_database_engine(database_url: str | None = None) -> Engine:
    url = _normalize_database_url(database_url or get_database_url())
    return create_engine(url, pool_pre_ping=True)
