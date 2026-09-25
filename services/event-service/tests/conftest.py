import pytest
import responses

from app import create_app
from validator import assert_matches_contract


@pytest.fixture(params=["memory", "json", "sqlite"])
def api(request, tmp_path):
    application = create_app({
        "STORAGE_BACKEND": request.param, "DATA_DIR": tmp_path,
        "USER_SERVICE_URL": "http://users.test:9001", "PORT": 5002,
    })
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture
def contract():
    def check(response, method, path, status=200):
        assert response.status_code == status, response.get_data(as_text=True)
        body = response.get_json() if response.data else None
        assert_matches_contract("event-service", method, path, {
            "status_code": response.status_code,
            "headers": dict(response.headers), "json": body,
        })
        return body
    return check


@pytest.fixture
def payload():
    return {
        "title": "Tech Conference", "organizer_id": "12345678-1234-4234-8234-123456789abc",
        "venue": "Auditorium", "city": "Trento", "start_date": "2026-11-10",
        "end_date": "2026-11-11", "capacity": 100, "price": 149.0,
    }


@pytest.fixture
def users_http(payload):
    with responses.RequestsMock() as mock:
        mock.get(f"http://users.test:9001/api/v1/users/{payload['organizer_id']}",
                 json={"role": "organizer"})
        yield mock


@pytest.fixture
def create_event(api, payload, users_http):
    def create(**overrides):
        response = api.post("/api/v1/events", json={**payload, **overrides})
        assert response.status_code == 201, response.get_json()
        return response.get_json()
    return create
