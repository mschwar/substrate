
# Implementation Plan (Solo Builder + AI Agents)

**Phase 0: Foundation** (2-4 weeks)

- Vault structure + YAML schema validator
- Basic file reader/writer with canonicalization
- ID generation (ULID monotonic)
- Quarantine + repair tools

**Phase 1: Canonical Editor** (4-6 weeks)

- Item view + editable frontmatter
- Inbox + basic capture (text note)
- Daily notes support

**Phase 2: Retrospective Import** (6-8 weeks)

- Folder importer
- Raw archive
- Basic extraction + stubs
- Metadata heuristics + observed claims
- Import job UI

**Phase 3: Enrichment & Indexing** (6-8 weeks)

- Local embedding pipeline
- Vector store integration
- Hybrid search
- Dedupe engine
- Backlinks index

**Phase 4: Prospective Capture** (4-6 weeks)

- Photo/voice/web clip workflows
- Transcription + OCR
- Inbox promotion flow

**Phase 5: AI & API** (4 weeks)

- RAG Q&A
- Local API (read + inbox write)
- Timeline view

**Phase 6: Polish & Hardening** (4 weeks)

- Privacy controls
- Export/prune
- Conflict handling
- Full CLI suite
- Accessibility pass

**Total Estimate**: 6-9 months to usable MVP

**Risk Mitigation**

- Build rebuildability early
- Test with real user data subsets
- All ops undoable or logged