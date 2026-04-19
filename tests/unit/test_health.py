from fastapi.testclient import TestClient

from app.main import app
from app.utils import REQUEST_ID_HEADER_NAME


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers[REQUEST_ID_HEADER_NAME].startswith("req_")
