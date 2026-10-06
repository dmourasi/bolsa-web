from fastapi.testclient import TestClient

from bolsa_web.web.app import create_app


def test_healthz_reports_ok_without_external_calls() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
