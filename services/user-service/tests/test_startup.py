"""REQ-USR-07, REQ-USR-09: issue #6, startup must not depend on reverse DNS."""
import runpy
import socket
import threading
from unittest.mock import patch

import pytest
import requests
from flask import Flask


pytestmark = pytest.mark.req("REQ-USR-09")


def test_main_starts_when_reverse_dns_is_unavailable(monkeypatch):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    monkeypatch.setenv("PORT", str(port))
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    with patch("socket.getfqdn", side_effect=RuntimeError("reverse DNS unavailable")), \
         patch("werkzeug.serving.BaseWSGIServer.serve_forever") as serve:
        runpy.run_module("app.__main__", run_name="__main__")
    serve.assert_called_once()
    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0


@pytest.mark.parametrize("debug", ["0", "1"])
def test_main_ignores_flask_debug_env(monkeypatch, debug):
    """Issue #2: real HTTP health on PORT, without debugger or reloader."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    monkeypatch.setenv("PORT", str(port))
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.setenv("FLASK_DEBUG", debug)
    served = []

    def serve_one(server):
        assert server.server_address == ("127.0.0.1", port)
        assert isinstance(server.app, Flask)
        assert server.app.debug is False
        server.timeout = 2
        worker = threading.Thread(target=server.handle_request, daemon=True)
        worker.start()
        try:
            with requests.get(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                assert response.status_code == 200
                assert response.json() == {"status": "ok", "service": "user-service"}
                served.append(True)
        finally:
            worker.join(timeout=3)
        assert not worker.is_alive()

    with patch("werkzeug.serving.BaseWSGIServer.serve_forever", serve_one), \
         patch("werkzeug._reloader.run_with_reloader", side_effect=AssertionError("reloader enabled")):
        runpy.run_module("app.__main__", run_name="__main__")
    assert served == [True]
    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0
