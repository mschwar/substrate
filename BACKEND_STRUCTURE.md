
# Backend Structure

**Core Components**

- Vault watcher (filesystem events)
- Import engine (job queue, resumable, idempotent)
- Enrich pipeline (OCR, transcription, entity, tag suggestions)
- Index manager (vectors, BM25, backlinks – rebuildable)
- Dedupe engine
- Local API server
- Ops log (append-only JSONL)

**Data Flow**

- All writes validated against schema v0.1
- Canonical files = source of truth
- Indexes derived and deletable

**Key Directories**

- _system/config.yaml
- _system/logs/
- jobs/<id>/

**Validation**

- Strict YAML parsing rules
- Write-time full validation
- Quarantine for unreadable files

**Error Handling**

- Never silent failure
- Structured logs
- UI notifications for critical

