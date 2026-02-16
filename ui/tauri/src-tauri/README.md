# Rust Backend Placeholder

This directory contains a minimal Tauri command registry stub. Commands are
registered in `src/main.rs` and defined in `src/commands.rs`.

The current stubs call a local HTTP API directly using `reqwest`.

Environment variables:
- `SUBSTRATE_API` (default `http://127.0.0.1:8123`)
- `SUBSTRATE_TOKEN` (optional auth token)
