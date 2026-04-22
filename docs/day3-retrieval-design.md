# Day 3 Retrieval Design

## Goal
Define what the system knows, how documents are represented, and how retrieval returns evidence for citation-grounded answers.

## Scope
This design covers local document retrieval for:
- annual reports
- earnings reports
- investor presentations
- research PDFs

Web retrieval remains a fallback path when local confidence is low.

## Document Sources (Final)
Primary source inventory is organized under `data/`:
- `data/tesla/annual`
- `data/tesla/earnings`
- `data/tesla/presentations`
- `data/apple/annual`
- `data/apple/earnings`
- `data/apple/presentations`
- `data/nvidia/annual`
- `data/nvidia/earnings`
- `data/nvidia/presentations`
- `data/research`

### Source Priority
1. Official filings and annual reports
2. Official earnings releases/transcripts
3. Official investor presentations
4. Curated research PDFs
5. Web fallback (only when evidence is insufficient)

## Retrieval Pipeline (v1)
1. Ingest PDFs and extract page text with stable page numbering.
2. Detect section boundaries where possible (heading heuristics + PDF layout cues).
3. Chunk text using recursive chunking with overlap.
4. Attach metadata at chunk level.
5. Generate embeddings.
6. Upsert embeddings and metadata into FAISS + SQLite.
7. Retrieve top-k candidates by semantic similarity.
8. Apply metadata filters (company/year/source_type/trust_tier) when provided.
9. Re-rank lightweight in application logic (similarity + trust tier + recency weights).
10. Return evidence bundle to synthesizer with citation fields.

## Query-Time Retrieval Policy
- Default `k = 12` initial retrieval.
- Keep top `6-8` chunks after metadata-aware re-ranking.
- Prefer diversity across documents/pages to avoid repeated evidence.
- Require at least `2` supporting chunks for high-confidence answers.
- Trigger fallback flow when:
  - no chunk exceeds similarity threshold, or
  - evidence conflicts strongly across trusted sources.

## Confidence Signals (for downstream critic)
- Max similarity score
- Mean of top-3 similarity scores
- Number of unique documents in evidence set
- Trust-tier weighted evidence score

## Acceptance Criteria
- Retrieval returns citation-ready chunks with page numbers.
- Metadata filters work for company/year/source_type.
- At least one successful end-to-end query per company (Tesla, Apple, Nvidia).
- Low-evidence queries route to controlled fallback behavior.
