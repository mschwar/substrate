# Frontend Mock

This mock UI pulls data from the local API exposed by `tools/api_fastapi.py`.

Run (recommended):

```bash
pip install -r requirements-api.txt
python tools/api_fastapi.py --vault /path/to/vault --port 8123 --token optional-token
python tools/serve_ui.py --root ui/tauri/src --port 8000 --token optional-token
```

Fallback (deprecated):

```bash
python tools/api_server.py --vault /path/to/vault --port 8123 --token optional-token
python tools/serve_ui.py --root ui/tauri/src --port 8000 --token optional-token
```

Then open http://127.0.0.1:8000 in a browser.

Features:
- Inbox list (live) + filters (status/privacy)
- Item view (live) + promote button
- Quick capture form
- Simple search (live) with filters
- Editor validate + save flows (`/api/validate`, `/api/item/update`)
- Daily open + append flows (`/api/daily/open`, `/api/daily/append`)
