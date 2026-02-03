
# Master Brief: Local-First Personal Data Substrate

**Project Codename**: Substrate **Version**: MVP v0.1 **Date**: February 2026 **Author**: Matthew Schwartz **Status**: Canonical Specification

### Core Purpose

Build a **local-first, single-user personal data substrate** that:

- Ingests messy historical data (retrospective phase)
- Captures new data in an AI-native way (prospective phase)
- Exposes the unified corpus through rebuildable indexes (semantic search, filtered search, timeline, lightweight graph)
- Enables reliable RAG/agent retrieval with full citations and provenance

The system is designed as a **trustworthy external memory** that is private-by-default, durable, reversible, and agent-safe.

### Target User (MVP)

One power-curious but time-poor individual who:

- Uses multiple devices
- Has accumulated digital exhaust across silos
- Wants faster retrieval than manual browsing
- Desires higher-level questions over their own history ("what changed", "patterns")
- Values privacy, portability, and vendor independence

Technical profile:

- Can follow instructions and run packaged apps
- Comfortable with folders, tags, search, sync concepts
- Does not identify as a developer

Emotional UX non-negotiables:

- Safe (no leaks, no surprises)
- Reversible (undo, rebuild, recover)
- Non-judgmental (messy is allowed)
- Useful within week 1

### Unique Value Proposition

Existing tools (Obsidian, Logseq, Notion, Evernote, etc.) excel at note-taking or graphs but fail at **end-to-end retrospective + prospective unification** with:

- Forensic ingestion at scale with provenance tracking
- Rebuildable AI layers (swap models, re-chunk, re-OCR without corrupting human corpus)
- Agent-safe data contract (read with citations, write only to inbox, never mutate originals)
- Cross-silo deduplication and identity reconciliation
- Temporal truth via competing metadata claims

### Scope Boundaries (MVP)

- Strictly single-user
- No multi-user collaboration or social features
- No real-time API scraping or always-on surveillance
- Bring-your-own-sync only
- Desktop (macOS, Windows, Linux) + CLI; mobile capture via folder sync
- Fully offline, zero mandatory cloud

### Success North Star

The user can reliably answer:

- "Find X"
- "What did I decide about Y and when?"
- "Show me the source"

With trust, calm, and minimal anxiety about lost information.
