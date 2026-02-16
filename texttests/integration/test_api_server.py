from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from substrate.io import parse_frontmatter


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


def _start_server(vault_root: Path, port: int, token: str | None = None) -> subprocess.Popen:
    root = _repo_root()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    cmd = [
        sys.executable,
        "tools/api_server.py",
        "--port",
        str(port),
        "--vault",
        str(vault_root),
    ]
    if token:
        cmd.extend(["--token", token])
    return subprocess.Popen(
        cmd,
        cwd=str(root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for(
    url: str,
    proc: subprocess.Popen,
    timeout: float = 3.0,
    headers: dict[str, str] | None = None,
) -> None:
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise AssertionError(f"Server exited early: {stderr}")
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=0.5):
                return
        except Exception:
            time.sleep(0.1)
    raise AssertionError("Server did not start")


def _json_get(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=1.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _json_post(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=1.0) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _expect_http_error(status: int, func) -> urllib.error.HTTPError:
    with pytest.raises(urllib.error.HTTPError) as exc:
        func()
    assert exc.value.code == status
    return exc.value


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


def test_api_server_validate_and_update(vault_root: Path):
    try:
        port = _pick_port()
    except PermissionError:
        pytest.skip("Socket binding not permitted in this environment")

    proc = _start_server(vault_root, port)
    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_for(f"{base_url}/api/inbox", proc)

        capture = _json_post(
            f"{base_url}/api/capture",
            {"title": "API Note", "body": "hello"},
        )
        path = capture["path"]
        item = _json_get(f"{base_url}/api/item?path={urllib.parse.quote(path)}")
        frontmatter = item["frontmatter"]
        body = item["body"]

        valid = _json_post(
            f"{base_url}/api/validate",
            {"frontmatter": frontmatter, "body": body},
        )
        assert valid["valid"] is True
        assert valid["errors"] == []
        assert isinstance(valid.get("warnings"), list)

        invalid_frontmatter = dict(frontmatter)
        invalid_frontmatter["status"] = "not-a-status"
        invalid = _json_post(
            f"{base_url}/api/validate",
            {"frontmatter": invalid_frontmatter, "body": body},
        )
        assert invalid["valid"] is False
        assert invalid["errors"]

        original_text = Path(path).read_text(encoding="utf-8")
        validate_only_frontmatter = dict(frontmatter)
        validate_only_frontmatter["title"] = "Validate Only"
        validate_only = _json_post(
            f"{base_url}/api/item/update",
            {
                "path": path,
                "frontmatter": validate_only_frontmatter,
                "body": body + "\nValidate only",
                "validate_only": True,
            },
        )
        assert validate_only["saved"] is False
        assert Path(path).read_text(encoding="utf-8") == original_text

        _expect_http_error(
            400,
            lambda: _json_post(
                f"{base_url}/api/item/update",
                {
                    "path": path,
                    "frontmatter": invalid_frontmatter,
                    "body": body,
                    "validate_only": True,
                },
            ),
        )
        assert Path(path).read_text(encoding="utf-8") == original_text

        saved_frontmatter = dict(frontmatter)
        saved_frontmatter["title"] = "Saved Title"
        saved = _json_post(
            f"{base_url}/api/item/update",
            {
                "path": path,
                "frontmatter": saved_frontmatter,
                "body": body + "\nSaved",
                "validate_only": False,
            },
        )
        assert saved["saved"] is True
        parsed = parse_frontmatter(Path(path).read_text(encoding="utf-8"))
        assert parsed.frontmatter["title"] == "Saved Title"
        assert "Saved" in parsed.body
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_api_server_daily_open_append(vault_root: Path):
    try:
        port = _pick_port()
    except PermissionError:
        pytest.skip("Socket binding not permitted in this environment")

    proc = _start_server(vault_root, port)
    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_for(f"{base_url}/api/inbox", proc)

        opened = _json_get(f"{base_url}/api/daily/open?date=2026-02-03")
        path = opened["path"]
        assert Path(path).exists()
        assert opened["item"]["frontmatter"]["type"] == "daily"
        assert opened["item"]["title"] == "2026-02-03"

        appended = _json_post(
            f"{base_url}/api/daily/append",
            {"date": "2026-02-03", "text": "Entry"},
        )
        assert appended["path"] == path
        assert "Entry" in appended["item"]["body"]
        assert "Entry" in Path(path).read_text(encoding="utf-8")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_api_server_editor_endpoints_require_token(vault_root: Path):
    try:
        port = _pick_port()
    except PermissionError:
        pytest.skip("Socket binding not permitted in this environment")

    token = "secret-token"
    proc = _start_server(vault_root, port, token=token)
    try:
        base_url = f"http://127.0.0.1:{port}"
        headers = {"X-Substrate-Token": token}
        _wait_for(f"{base_url}/api/inbox", proc, headers=headers)

        _expect_http_error(
            401,
            lambda: _json_post(
                f"{base_url}/api/validate",
                {"frontmatter": {}, "body": ""},
            ),
        )
        _expect_http_error(
            401,
            lambda: _json_post(
                f"{base_url}/api/item/update",
                {
                    "path": "missing",
                    "frontmatter": {},
                    "body": "",
                    "validate_only": True,
                },
            ),
        )
        _expect_http_error(
            401,
            lambda: _json_get(f"{base_url}/api/daily/open?date=2026-02-03"),
        )
        _expect_http_error(
            401,
            lambda: _json_post(
                f"{base_url}/api/daily/append",
                {"date": "2026-02-03", "text": "Entry"},
            ),
        )

        opened = _json_get(f"{base_url}/api/daily/open?date=2026-02-03", headers=headers)
        assert opened["path"]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
