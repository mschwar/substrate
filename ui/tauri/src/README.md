# Frontend Mock

This mock UI pulls data from the local API exposed by `tools/api_server.py`.

Run:

```bash
python tools/api_server.py --vault /path/to/vault --port 8123
python tools/serve_ui.py --root ui/tauri/src --port 8000
```

Then open http://127.0.0.1:8000 in a browser.

Features:
- Inbox list (live) + filters (status/privacy)
- Item view (live) + promote button
- Quick capture form
- Simple search (live) with filters
