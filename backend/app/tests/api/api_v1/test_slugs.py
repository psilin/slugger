from app.core.config import settings
from fastapi.testclient import TestClient


def test_overview_wrong_limit(client: TestClient) -> None:
    response = client.get(settings.API_PREFIX + "/overview?limit=-1")
    assert response.status_code == 422
    content = response.json()
    assert content["errors"] == ["Limit query parameter should be >= 1."]


def test_overview_wrong_page(client: TestClient) -> None:
    response = client.get(settings.API_PREFIX + "/overview?page=-1")
    assert response.status_code == 422
    content = response.json()
    assert content["errors"] == ["Page query parameter should be >= 1."]
