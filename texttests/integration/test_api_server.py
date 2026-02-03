from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pick_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("", 0))
    except PermissionError as exc:
        sock.close()
        raise exc
    port = sock.getsockname()[1]
    sock.close()
    return port


def _start_server(vault_root: Path, port: int) -> subprocess.Popen:
    root = _repo_root()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    return subprocess.Popen(
        [
            sys.executable,
            "tools/api_server.py",
            "--port",
            str(port),
            "--vault",
            str(vault_root),
        ],
        cwd=str(root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for(url: str, proc: subprocess.Popen, timeout: float = 3.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise AssertionError(f"Server exited early: {stderr}")
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                return
        except Exception:
            time.sleep(0.1)
    raise AssertionError("Server did not start")


def test_api_server_capture_and_search(vault_root: Path):
    try:
        port = _pick_port()
    except PermissionError:
        pytest.skip("Socket binding not permitted in this environment")

    proc = _start_server(vault_root, port)
    try:
        _wait_for(f"http://127.0.0.1:{port}/api/inbox", proc)

        payload = json.dumps({"title": "API Note", "body": "hello"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/capture",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert "path" in data

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/search?q=hello", timeout=1.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["total"] >= 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
