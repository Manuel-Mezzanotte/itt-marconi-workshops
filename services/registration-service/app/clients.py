import math

import requests

from app.errors import ApiError


class ReferenceClients:
    def __init__(self, user_url, event_url):
        self.user_url = user_url.rstrip("/")
        self.event_url = event_url.rstrip("/")

    def _get(self, base_url, resource, identifier, missing_status=422):
        unavailable = ApiError(503, "DEPENDENCY_UNAVAILABLE", f"{resource} service is unavailable")
        try:
            with requests.get(
                f"{base_url}/api/v1/{resource}/{identifier}", timeout=2, allow_redirects=False,
            ) as response:
                if response.status_code == 404:
                    code = "NOT_FOUND" if missing_status == 404 else "REFERENCE_NOT_FOUND"
                    raise ApiError(missing_status, code, f"Referenced {resource} resource does not exist")
                if response.status_code != 200:
                    raise unavailable
                body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise unavailable from exc
        if not isinstance(body, dict) or body.get("id") != identifier:
            raise unavailable
        return body

    def get_user(self, user_id):
        return self._get(self.user_url, "users", user_id)

    def get_event(self, event_id, missing_status=422):
        event = self._get(self.event_url, "events", event_id, missing_status)
        status, capacity, price = event.get("status"), event.get("capacity"), event.get("price")
        try:
            valid = (
                isinstance(status, str) and status in {"draft", "published", "cancelled"}
                and type(capacity) is int and 1 <= capacity <= 10000
                and type(price) in (int, float) and price >= 0 and math.isfinite(price)
            )
        except OverflowError:
            valid = False
        if not valid:
            raise ApiError(503, "DEPENDENCY_UNAVAILABLE", "event-service returned invalid event data")
        return event
