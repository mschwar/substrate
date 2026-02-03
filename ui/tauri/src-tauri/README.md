# Rust Backend Placeholder

This directory contains a minimal Tauri command registry stub. Commands are
registered in `src/main.rs` and defined in `src/commands.rs`.

The current stubs route to the Python bridge (`tools/tauri_bridge.py`) so the UI
can access the same local API as the mock server. This is a temporary shim until
we embed the API directly in Rust.
