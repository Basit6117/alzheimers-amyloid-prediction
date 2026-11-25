"""HTTP integration tests for the isolated prediction endpoint."""

import json
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def api_url() -> Iterator[str]:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(30):
            try:
                with urlopen(f"{base_url}/api/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"Prediction API did not start: {stderr}")
        yield base_url
    finally:
        process.terminate()
        process.wait(timeout=10)


def _post_json(url: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def test_predict_valid_input(api_url: str) -> None:
    status, body = _post_json(
        f"{api_url}/api/predict",
        {
            "pT217_F": 0.386,
            "AB42_AB40_F": 0.0973,
            "GFAP_Q": 175.1418,
            "APOE4": 0,
            "AGE": 73.0,
            "SEX": 1,
        },
    )

    assert status == 200
    assert set(body) == {"probability", "category", "top_factors", "model_version"}
    assert 0.0 <= float(body["probability"]) <= 1.0
    assert body["category"] in {"Low", "Moderate", "Elevated"}
    assert len(body["top_factors"]) == 3
    assert body["model_version"] == "amyloid_svm_champion_9306"


def test_predict_rejects_missing_field(api_url: str) -> None:
    status, _ = _post_json(
        f"{api_url}/api/predict",
        {"pT217_F": 0.386, "GFAP_Q": 175.1418},
    )

    assert status == 422


def test_predict_rejects_out_of_range_value(api_url: str) -> None:
    status, _ = _post_json(
        f"{api_url}/api/predict",
        {
            "pT217_F": 2.0,
            "AB42_AB40_F": 0.0973,
            "GFAP_Q": 175.1418,
            "APOE4": 0,
            "AGE": 73.0,
            "SEX": 1,
        },
    )

    assert status == 422
