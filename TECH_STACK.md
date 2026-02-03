
# Technology Stack (MVP Constraints)

**Core Language**: Python 3.12 (pure-Python where possible for portability)

**UI Framework**

- Lightweight desktop: Prefer Tauri (Rust core + web frontend) over Electron for size/performance
- Alternative fallback: Dear PyGui or PyQt6 if Tauri integration too complex

**Storage**

- Filesystem vault (markdown + attachments)
- Raw archive (BLAKE3 content-addressed)

**Indexing**

- Vector store: Chroma or LanceDB (persistent, metadata filtering)
- Full-text: built-in or lightweight (e.g., tantivy via pyo3 if needed)
- Backlinks/graph: filesystem watcher + on-disk index

**AI/ML**

- Embeddings: locked default English model (nomic-embed or bge-small, downloadable)
- Transcription: local Whisper (small/base via faster-whisper or whisper.cpp)
- OCR: local Tesseract or Mango (if available)

**Cryptography/Hashing**

- BLAKE3 primary
- SHA-256 optional interoperability

**API**

- Local HTTP (FastAPI or similar) bound to 127.0.0.1

**CLI**

- Built with click or argparse, structured JSONL logs

**Plugins**

- Python drop-in modules

**Dependencies Principles**

- Minimize native deps
- All critical ops scriptable via CLI
- No mandatory cloud

