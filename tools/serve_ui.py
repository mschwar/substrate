from __future__ import annotations

import argparse
import http.server
import json
import socketserver
import urllib.parse
from pathlib import Path
from urllib.request import Request, urlopen


def _json_response(handler: http.server.SimpleHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _error(handler: http.server.SimpleHTTPRequestHandler, message: str, status: int = 400) -> None:
    _json_response(handler, {"error": message}, status=status)


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def _proxy_get(api: str, path: str, token: str | None) -> dict:
    req = Request(api + path)
    if token:
        req.add_header("X-Substrate-Token", token)
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _proxy_post(api: str, path: str, payload: dict, token: str | None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(api + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
    if token:
        req.add_header("X-Substrate-Token", token)
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def make_handler(ui_root: Path, api_base: str | None, token: str | None):
    class SubstrateHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ui_root), **kwargs)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path.startswith("/api/"):
                if api_base is None:
                    _error(self, "api base not configured", status=500)
                    return
                try:
                    payload = _proxy_get(api_base, parsed.path + ("?" + parsed.query if parsed.query else ""), token)
                except Exception as exc:
                    _error(self, f"api error: {exc}", status=502)
                    return
                _json_response(self, payload)
                return

            return super().do_GET()

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            if not parsed.path.startswith("/api/"):
                self.send_error(404)
                return
            if api_base is None:
                _error(self, "api base not configured", status=500)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                _error(self, "empty request body", status=400)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                _error(self, "invalid JSON", status=400)
                return
            try:
                data = _proxy_post(api_base, parsed.path, payload, token)
            except Exception as exc:
                _error(self, f"api error: {exc}", status=502)
                return
            _json_response(self, data)

    return SubstrateHandler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--root", default="ui/tauri/src")
    parser.add_argument("--api", help="API base URL", default="http://127.0.0.1:8123")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--vault", help="Vault root (to load API token)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"UI root not found: {root}")

    token = args.token
    if token is None and args.vault:
        try:
            from substrate.config import load_api_token
        except Exception:
            load_api_token = None
        if load_api_token is not None:
            token = load_api_token(Path(args.vault))

    handler = make_handler(root, args.api, token)
    with ReuseTCPServer(("", args.port), handler) as httpd:
        print(f"Serving {root} at http://127.0.0.1:{args.port}")
        print(f"Proxying API to {args.api}")
        if token:
            print("Proxying with API token")
        httpd.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
