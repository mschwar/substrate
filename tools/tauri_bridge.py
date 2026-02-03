from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8123")
    parser.add_argument("command")
    parser.add_argument("payload", nargs="?")
    args = parser.parse_args()

    payload = json.loads(args.payload) if args.payload else {}
    api = args.api.rstrip("/")

    if args.command == "inbox_view":
        params = "&".join(
            f"{key}={urllib.parse.quote(str(value))}"
            for key, value in {
                "limit": payload.get("limit", 20),
                "offset": payload.get("offset", 0),
                "sort": payload.get("sort", "updated_desc"),
                "status": payload.get("status", ""),
                "privacy": payload.get("privacy", ""),
            }.items()
        )
        result = _get(f"{api}/api/inbox?{params}")
    elif args.command == "item_view":
        path = payload.get("path", "")
        result = _get(f"{api}/api/item?path={urllib.parse.quote(path)}")
    elif args.command == "search":
        params = "&".join(
            f"{key}={urllib.parse.quote(str(value))}"
            for key, value in {
                "q": payload.get("query", ""),
                "limit": payload.get("limit", 20),
                "offset": payload.get("offset", 0),
                "status": payload.get("status", ""),
                "privacy": payload.get("privacy", ""),
            }.items()
        )
        result = _get(f"{api}/api/search?{params}")
    elif args.command == "capture":
        result = _post(f"{api}/api/capture", payload)
    elif args.command == "promote":
        result = _post(f"{api}/api/promote", payload)
    else:
        print(json.dumps({"error": "unknown command"}))
        return 1

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
