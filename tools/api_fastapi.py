from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, Header, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from starlette.exceptions import HTTPException as StarletteHTTPException
except Exception as exc:  # pragma: no cover
    raise SystemExit("fastapi is required to run this server") from exc

import uvicorn

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


def _token(header_token: str | None, query_token: str | None) -> str | None:
    return header_token or query_token or None


async def _read_payload(request: Request) -> dict:
    body = await request.body()
    if not body:
        raise ApiError("empty request body", status=400)
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as exc:
        raise ApiError("invalid JSON", status=400) from exc
    if not isinstance(payload, dict):
        raise ApiError("payload must be an object", status=400)
    return payload


def create_app(vault_root: Path, token_required: str | None) -> FastAPI:
    app = FastAPI()

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return JSONResponse({"error": exc.message}, status_code=exc.status)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        message = exc.detail
        if exc.status_code == 404 and exc.detail == "Not Found":
            message = "not found"
        return JSONResponse({"error": message}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse({"error": "invalid request"}, status_code=400)

    @app.get("/api/inbox")
    async def inbox(
        limit: int = 20,
        offset: int = 0,
        sort: str = "updated_desc",
        status: str | None = None,
        privacy: str | None = None,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return api_inbox(
            vault_root,
            limit=limit,
            offset=offset,
            sort=sort,
            status=_parse_csv(status),
            privacy=_parse_csv(privacy),
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.get("/api/item")
    async def item(
        path: str,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return api_item(
            vault_root,
            path_value=path,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.get("/api/search")
    async def search(
        q: str = "",
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        privacy: str | None = None,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return api_search(
            vault_root,
            query=q,
            limit=limit,
            offset=offset,
            status=_parse_csv(status),
            privacy=_parse_csv(privacy),
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.get("/api/daily/open")
    async def daily_open(
        date: str | None = None,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return api_daily_open(
            vault_root,
            date_value=date,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.post("/api/daily/open")
    async def daily_open_post(
        request: Request,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        payload = await _read_payload(request)
        return api_daily_open(
            vault_root,
            date_value=payload.get("date"),
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.post("/api/capture")
    async def capture(
        request: Request,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        payload = await _read_payload(request)
        return api_capture(
            vault_root,
            payload=payload,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.post("/api/promote")
    async def promote(
        request: Request,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        payload = await _read_payload(request)
        return api_promote(
            vault_root,
            payload=payload,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.post("/api/validate")
    async def validate(
        request: Request,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        payload = await _read_payload(request)
        return api_validate(
            vault_root,
            payload=payload,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.post("/api/item/update")
    async def item_update(
        request: Request,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        payload = await _read_payload(request)
        return api_item_update(
            vault_root,
            payload=payload,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    @app.post("/api/daily/append")
    async def daily_append(
        request: Request,
        token: str | None = None,
        x_substrate_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        payload = await _read_payload(request)
        return api_daily_append(
            vault_root,
            payload=payload,
            token_required=token_required,
            token_provided=_token(x_substrate_token, token),
        )

    return app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--vault", required=True, help="Vault root")
    parser.add_argument("--token", help="API token (optional)")
    args = parser.parse_args()

    vault_root = Path(args.vault).resolve()
    token = args.token or load_api_token(vault_root)
    app = create_app(vault_root, token)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
