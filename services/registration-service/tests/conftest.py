import pytest

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
