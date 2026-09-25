"""REQ-USR-12: all seven declared API operations, on every storage backend."""
import pytest


pytestmark = pytest.mark.req("REQ-USR-12")
BASE = "/api/v1/users"


def test_complete_user_lifecycle_matches_contract(api, contract):
    assert contract(api.get("/health"), "GET", "/health") == {
        "status": "ok", "service": "user-service",
    }
    payload = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
    response = api.post(BASE, json=payload)
    user = contract(response, "POST", BASE, 201)
    path = response.headers["Location"]
    assert path == f"{BASE}/{user['id']}"
    assert contract(api.get(path), "GET", path) == user
    assert contract(api.get(BASE), "GET", BASE)["items"] == [user]
    replaced = contract(api.put(path, json={**payload, "company": "New Co"}), "PUT", path)
    assert replaced["company"] == "New Co"
    updated = contract(api.patch(path, json={"role": "speaker"}), "PATCH", path)
    assert updated["role"] == "speaker" and updated["company"] == "New Co"
    assert contract(api.get(path), "GET", path) == updated
    assert contract(api.delete(path), "DELETE", path, 204) is None
    assert contract(api.get(BASE), "GET", BASE)["total"] == 0
