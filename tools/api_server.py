from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from substrate.io import canonicalize_path
from substrate.items import create_inbox_note, promote_inbox_item
from substrate.views import inbox_view, load_item_view, search_view


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


def make_handler(vault_root: Path):
    class APIHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            if parsed.path == "/api/inbox":
                limit = int(query.get("limit", ["20"])[0])
                offset = int(query.get("offset", ["0"])[0])
                sort = query.get("sort", ["updated_desc"])[0]
                status = _parse_csv(query.get("status", [""])[0])
                privacy = _parse_csv(query.get("privacy", [""])[0])
                try:
                    payload = inbox_view(
                        vault_root,
                        limit=limit,
                        offset=offset,
                        sort=sort,
                        status=status,
                        privacy=privacy,
                    )
                except ValueError as exc:
                    _error(self, str(exc), status=400)
                    return
                _json_response(self, payload)
                return

            if parsed.path == "/api/item":
                path_value = query.get("path", [""])[0]
                if not path_value:
                    _error(self, "missing path parameter", status=400)
                    return
                try:
                    path = canonicalize_path(vault_root, Path(path_value))
                except ValueError:
                    _error(self, "invalid path", status=400)
                    return
                if not path.exists():
                    _error(self, "path not found", status=404)
                    return
                payload = load_item_view(path)
                _json_response(self, payload)
                return

            if parsed.path == "/api/search":
                q = query.get("q", [""])[0]
                limit = int(query.get("limit", ["20"])[0])
                offset = int(query.get("offset", ["0"])[0])
                status = _parse_csv(query.get("status", [""])[0])
                privacy = _parse_csv(query.get("privacy", [""])[0])
                payload = search_view(vault_root, q, limit=limit, offset=offset, status=status, privacy=privacy)
                _json_response(self, payload)
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

            if parsed.path == "/api/capture":
                title = str(payload.get("title", "")).strip()
                body = str(payload.get("body", ""))
                tags = payload.get("tags")
                privacy = str(payload.get("privacy", "private"))
                if tags is not None and not isinstance(tags, list):
                    _error(self, "tags must be an array", status=400)
                    return
                if not title:
                    _error(self, "title is required", status=400)
                    return
                path = create_inbox_note(
                    vault_root,
                    title=title,
                    body=body,
                    tags=tags,
                    privacy=privacy,
                )
                _json_response(self, {"path": str(path)})
                return

            if parsed.path == "/api/promote":
                path_value = str(payload.get("path", ""))
                status_value = str(payload.get("status", "canonical"))
                if not path_value:
                    _error(self, "path is required", status=400)
                    return
                try:
                    path = canonicalize_path(vault_root, Path(path_value))
                except ValueError:
                    _error(self, "invalid path", status=400)
                    return
                try:
                    target = promote_inbox_item(vault_root, path, target_status=status_value)
                except ValueError as exc:
                    _error(self, str(exc), status=400)
                    return
                _json_response(self, {"path": str(target)})
                return

            _error(self, "not found", status=404)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return APIHandler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--vault", required=True, help="Vault root")
    args = parser.parse_args()

    vault_root = Path(args.vault).resolve()
    handler = make_handler(vault_root)
    server = HTTPServer(("", args.port), handler)
    print(f"API server running at http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
