from app.database.connection import get_database_url
from app.agent.llm import get_model_name
from app.database.seed import _seed_connection_hint
from sqlalchemy.exc import OperationalError


def test_database_url_removes_repeated_assignment_prefix(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "DATABASE_URL=DATABASE_URL=postgresql+psycopg://user:secret@localhost:5432/soufet",
    )

    assert get_database_url() == "postgresql+psycopg://user:secret@localhost:5432/soufet"


def test_seed_reports_auth_failure_without_printing_credentials():
    error = OperationalError("connect", {}, Exception('password authentication failed for user "soufet"'))

    message = _seed_connection_hint(error)

    assert "rejected" in message
    assert "Remove-Item Env:DATABASE_URL" in message
    assert "secret" not in message


def test_default_nvidia_model_name(monkeypatch):
    monkeypatch.delenv("NVIDIA_MODEL", raising=False)

    assert get_model_name() == "nvidia/nemotron-3-ultra-550b-a55b"
