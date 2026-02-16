from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from substrate.api import (
    ApiError,
    api_capture,
    api_daily_append,
    api_daily_open,
    api_inbox,
    api_item,
    api_item_update,
    api_promote,
    api_search,
    api_validate,
)
from substrate.config import load_api_token


def _parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",")]
    cleaned = [part for part in parts if part]
    return cleaned or None


def _json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _error(handler: BaseHTTPRequestHandler, message: str, status: int = 400) -> None:
    _json_response(handler, {"error": message}, status=status)


def _extract_token(handler: BaseHTTPRequestHandler, query: dict) -> str | None:
    header = handler.headers.get("X-Substrate-Token")
    if header:
        return header
    token_param = query.get("token", [""])[0]
    return token_param or None


def make_handler(vault_root: Path, token_required: str | None):
    class APIHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            token = _extract_token(self, query)
            try:
                if parsed.path == "/api/inbox":
                    limit = int(query.get("limit", ["20"])[0])
                    offset = int(query.get("offset", ["0"])[0])
                    sort = query.get("sort", ["updated_desc"])[0]
                    status = _parse_csv(query.get("status", [""])[0])
                    privacy = _parse_csv(query.get("privacy", [""])[0])
                    payload = api_inbox(
                        vault_root,
                        limit=limit,
                        offset=offset,
                        sort=sort,
                        status=status,
                        privacy=privacy,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, payload)
                    return

                if parsed.path == "/api/item":
                    path_value = query.get("path", [""])[0]
                    payload = api_item(
                        vault_root,
                        path_value=path_value,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, payload)
                    return

                if parsed.path == "/api/search":
                    q = query.get("q", [""])[0]
                    limit = int(query.get("limit", ["20"])[0])
                    offset = int(query.get("offset", ["0"])[0])
                    status = _parse_csv(query.get("status", [""])[0])
                    privacy = _parse_csv(query.get("privacy", [""])[0])
                    payload = api_search(
                        vault_root,
                        query=q,
                        limit=limit,
                        offset=offset,
                        status=status,
                        privacy=privacy,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, payload)
                    return

                if parsed.path == "/api/daily/open":
                    date_value = query.get("date", [""])[0] or None
                    payload = api_daily_open(
                        vault_root,
                        date_value=date_value,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, payload)
                    return
            except ApiError as exc:
                _error(self, exc.message, status=exc.status)
                return

            _error(self, "not found", status=404)

        def do_POST(self):
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                _error(self, "empty request body", status=400)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                _error(self, "invalid JSON", status=400)
                return
            token = _extract_token(self, parse_qs(parsed.query))

            try:
                if parsed.path == "/api/capture":
                    data = api_capture(
                        vault_root,
                        payload=payload,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, data)
                    return

                if parsed.path == "/api/promote":
                    data = api_promote(
                        vault_root,
                        payload=payload,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, data)
                    return

                if parsed.path == "/api/validate":
                    data = api_validate(
                        vault_root,
                        payload=payload,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, data)
                    return

                if parsed.path == "/api/item/update":
                    data = api_item_update(
                        vault_root,
                        payload=payload,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, data)
                    return

                if parsed.path == "/api/daily/append":
                    data = api_daily_append(
                        vault_root,
                        payload=payload,
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, data)
                    return

                if parsed.path == "/api/daily/open":
                    data = api_daily_open(
                        vault_root,
                        date_value=payload.get("date"),
                        token_required=token_required,
                        token_provided=token,
                    )
                    _json_response(self, data)
                    return
            except ApiError as exc:
                _error(self, exc.message, status=exc.status)
                return

            _error(self, "not found", status=404)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return APIHandler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--vault", required=True, help="Vault root")
    parser.add_argument("--token", help="API token (optional)")
    args = parser.parse_args()

    vault_root = Path(args.vault).resolve()
    token = args.token or load_api_token(vault_root)
    handler = make_handler(vault_root, token)
    server = HTTPServer(("", args.port), handler)
    print(f"API server running at http://127.0.0.1:{args.port}")
    print("Deprecated: use tools/api_fastapi.py for the default server")
    if token:
        print("API token required")
    server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
