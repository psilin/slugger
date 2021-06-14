from typing import Generator

import pytest
from app.main import get_application
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> Generator:
    app = get_application(with_db=False)
    with TestClient(app) as c:
        yield c
