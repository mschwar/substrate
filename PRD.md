
# Product Requirements Document

**Version**: v0.1 (MVP) **Schema**: v0.1

### 1. Data Scope

**Tier 1 (MVP)**

- Notes (markdown/plain text)
- Documents (PDF, docx, txt, md)
- Photos + screenshots (EXIF + sidecar)
- Voice memos/audio (with transcription)
- Web clips (URL + extracted text)
- Local filesystem folders
- Export bundles (zip/tar)

**Tier 2 (v1+)**

- Email (mbox/eml)
- Calendar (ics)
- Contacts (vcf/csv)
- Chat exports

**Out of Scope**

- Real-time private API ingestion
- Continuous recording
- DRM-bypassing or ToS-violating sources

### 2. Storage Layers

**Layer 0: Raw Archive**

- Content-addressed (BLAKE3)
- Path: raw/blake3/<2-hex-prefix>/<full-hash>/original.ext + meta.json + optional extracts/thumbs
- Never auto-deleted

**Layer 1: Canonical Vault**

- Human-first, AI-ready markdown files
- Structure:
    
    text
    
    ```
    vault/
      inbox/
      daily/
      items/<id>.md
      entities/
      attachments/<id>/
      exports/
      _system/
    ```
    
- Frontmatter: strict YAML v0.1 schema (see separate schema doc)

### 3. Retrospective Phase Requirements

- Support: local folders, photo libraries (folder), export zips, mbox/eml, ics, vcf/csv
- Automation: discovery, hashing, extraction, dedupe suggestions, OCR/transcription/entity (review queue)
- Never destroy originals
- Metadata conflicts → observed[] claims + best-guess heuristics
- Prioritization presets: meaningful first, recent first, etc.

### 4. Prospective Phase Requirements

**Capture Workflows**

- Quick text note → inbox
- Daily journal append
- Photo/screenshot with auto-metadata
- Voice-to-text (local Whisper small/base)
- Web clip (Readability extraction)
- Drop folder

**Friction Targets**

- Mobile: ≤2 taps via share sheet (via sync folder)
- Desktop: global hotkey, drag/drop

### 5. AI Integration (MVP)

- Semantic search (hybrid BM25 + vector)
- Filtered search (all dimensions)
- RAG Q&A with structured citations
- Timeline summarization
- Dedupe suggestions
- Tag/entity suggestions
- Built-in local embedding generation + persistent vector store
- Local read-only API + write-only inbox endpoint
- Default local-only models

### 6. Privacy & Security

- Fully offline
- privacy: public | private | sensitive (sensitive never cloud, excluded from default exports)
- Derived artifacts inherit max privacy
- One-click full export
- Deletion controls with audit logs

### 7. Non-Functional Requirements

- Scale: 100k–1M items, 1–5 TB attachments
- Search latency: <300ms typical, <2s p95 at 1M
- Rebuildable indexes
- BYO sync with conflict handling

## APP_FLOW.md

# Application Flows

### 1. First Launch / Vault Creation

1. User selects or creates vault folder
2. App initializes _system/config.yaml (vault_timezone prompt)
3. Offers quick start: import a folder or capture first note

### 2. Retrospective Import Flow

1. User selects source (folder, zip, mbox, etc.)
2. Job queued with priority/preset
3. Background stages: discover → hash → extract → canonicalize → enrich → index
4. Progress UI with resumability
5. Errors → stubs + review queue
6. Dedupe suggestions post-import

### 3. Prospective Capture Flow (Desktop)

1. Global hotkey → capture window
2. Choose type (note default)
3. Enter text / paste / drop file / record voice
4. Item lands in inbox with status/inbox
5. Background enrich (transcription, OCR, suggestions)
6. User promotes → canonical

### 4. Inbox Processing Flow

1. Inbox view shows unprocessed + drafts
2. Batch actions: tag, privacy, promote
3. Promote triggers final enrich + move to items/

### 5. Search & Retrieval Flow

1. / hotkey → search bar
2. Type query + filters
3. Results with snippets + citations
4. Click → item view (provenance, backlinks)
5. RAG Q&A via command palette

### 6. Deduplication Flow

1. Dedupe view shows groups (transitive)
2. Preview diffs/overlays
3. Merge → primary survives, others tombstoned
4. Undo via ops log

### 7. Daily Journal Flow

1. Open daily note (auto-create if missing)
2. Append entries
3. Filename/created invariant enforced

