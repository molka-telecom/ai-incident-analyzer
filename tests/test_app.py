import pytest
from fastapi.testclient import TestClient

from app.logging_config import LOG_FILE
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("route", "status_code", "detail"),
    [
        ("/error/500", 500, "Internal server error"),
        ("/error/503", 503, "Service unavailable"),
        ("/error/504", 504, "Gateway timeout"),
    ],
)
def test_error_routes_return_expected_status(route, status_code, detail):
    response = client.get(route)

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


def test_error_routes_write_logs():
    client.get("/error/503")

    content = LOG_FILE.read_text(encoding="utf-8")
    assert "| WARNING | app.main | Database connection attempt failed" in content
    assert "| ERROR | app.main | Database unavailable" in content


def test_logs_are_written_to_temporary_directory():
    # Garantit que les tests ne polluent pas le vrai fichier logs/app.log
    assert "test-logs-" in str(LOG_FILE)
