import os
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests
from validator import assert_matches_contract


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ServiceProcess:
    name: str
    process: subprocess.Popen
    port: int
    data_dir: Path
    log: object

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.log.close()
        with socket.socket() as probe:
            probe.settimeout(1)
            assert probe.connect_ex(("127.0.0.1", self.port)) != 0


@pytest.fixture(params=["memory", "json", "sqlite"])
def backend(request):
    return request.param


@pytest.fixture
def start_service(backend):
    started = []
    with tempfile.TemporaryDirectory(prefix=f"techconf-http-{backend}-") as workspace:
        def start(name, *, urls=None, data_dir=None, port=None):
            if port is None:
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", 0))
                    port = probe.getsockname()[1]
            directory = Path(data_dir) if data_dir else Path(workspace) / f"{name}-{len(started)}"
            log_path = Path(workspace) / f"{name}-{len(started)}.log"
            log = log_path.open("w")
            environment = {
                **os.environ, "PORT": str(port), "STORAGE_BACKEND": backend,
                "DATA_DIR": str(directory), **(urls or {}),
            }
            try:
                process = subprocess.Popen(
                    [sys.executable, "-m", "app"], cwd=ROOT / "services" / name,
                    env=environment, stdout=log, stderr=subprocess.STDOUT,
                )
            except Exception:
                log.close()
                raise
            service = ServiceProcess(name, process, port, directory, log)
            started.append(service)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with requests.get(f"{service.url}/health", timeout=0.5) as response:
                        if response.status_code == 200:
                            return service
                except requests.RequestException:
                    pass
                time.sleep(0.05)
            service.stop()
            pytest.fail(f"{name} failed to start: {log_path.read_text()}")

        try:
            yield start
        finally:
            for service in reversed(started):
                service.stop()


@pytest.fixture
def event_platform(start_service):
    user = start_service("user-service")
    event = start_service("event-service", urls={"USER_SERVICE_URL": user.url})
    return user, event


@pytest.fixture
def http():
    def request(service, method, path, **kwargs):
        with requests.request(method, service.url + path, timeout=5, **kwargs) as response:
            assert_matches_contract(service.name, method, path, response)
            return response
    return request
