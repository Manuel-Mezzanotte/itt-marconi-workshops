import requests

from app.errors import ApiError


class UserClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def require_organizer(self, user_id):
        unavailable = ApiError(503, "DEPENDENCY_UNAVAILABLE", "user-service is unavailable")
        try:
            with requests.get(
                f"{self.base_url}/api/v1/users/{user_id}", timeout=2, allow_redirects=False,
            ) as response:
                if response.status_code == 404:
                    raise ApiError(422, "REFERENCE_NOT_FOUND", "Organizer does not exist")
                if response.status_code != 200:
                    raise unavailable
                user = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise unavailable from exc
        if not isinstance(user, dict) or not isinstance(user.get("role"), str):
            raise unavailable
        if user["role"] != "organizer":
            raise ApiError(422, "INVALID_ORGANIZER", "User must have role organizer")
