import pytest
import json
import re
import responses

from app import create_app
from validator import assert_matches_contract


@pytest.fixture(params=["memory", "json", "sqlite"])
def api(request, tmp_path):
    application = create_app({
        "STORAGE_BACKEND": request.param, "DATA_DIR": tmp_path, "PORT": 5003,
        "USER_SERVICE_URL": "http://users.test:9001", "EVENT_SERVICE_URL": "http://events.test:9002",
    })
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture
def contract():
    def check(response, method, path, status=200):
        assert response.status_code == status, response.get_data(as_text=True)
        body = response.get_json() if response.data else None
        assert_matches_contract("registration-service", method, path, {
            "status_code": response.status_code, "headers": dict(response.headers), "json": body,
        })
        return body
    return check


@pytest.fixture
def payload():
    return {
        "user_id": "00000000-0000-4000-8000-00000000000a",
        "event_id": "00000000-0000-4000-8000-00000000000b",
    }


@pytest.fixture
def event(payload):
    return {"id": payload["event_id"], "status": "published", "capacity": 2, "price": 149.0}


@pytest.fixture
def references(event):
    def user_response(request):
        return 200, {}, json.dumps({"id": request.url.rsplit("/", 1)[1], "role": "attendee"})

    def event_response(request):
        return 200, {}, json.dumps({**event, "id": request.url.rsplit("/", 1)[1]})

    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        mock.add_callback("GET", re.compile(r"http://users.test:9001/api/v1/users/[0-9a-f-]+$"),
                          callback=user_response, content_type="application/json")
        mock.add_callback("GET", re.compile(r"http://events.test:9002/api/v1/events/[0-9a-f-]+$"),
                          callback=event_response, content_type="application/json")
        yield mock


@pytest.fixture
def create_registration(api, payload, references):
    def create(**overrides):
        response = api.post("/api/v1/registrations", json={**payload, **overrides})
        assert response.status_code == 201, response.get_json()
        return response.get_json()
    return create
