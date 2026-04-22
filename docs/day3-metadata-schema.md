# Day 3 Metadata Schema (Final)

## Objective
Standardize chunk-level metadata so retrieval, filtering, and citations are reliable.

## Canonical Fields

| Field | Type | Required | Example | Notes |
|---|---|---|---|---|
| filename | TEXT | Yes | `tesla_2024_10k.pdf` | Original file name |
| company | TEXT | Yes | `tesla` | Controlled enum: `tesla`, `apple`, `nvidia`, `research` |
| year | INTEGER | Yes | `2024` | Reporting year; fallback to publish year |
| source_type | TEXT | Yes | `annual` | Enum: `annual`, `earnings`, `presentations`, `research` |
| page_number | INTEGER | Yes | `187` | 1-indexed source page |
| section_title | TEXT | No | `Management Discussion and Analysis` | Derived during parsing when available |
| upload_time | TEXT | Yes | `2026-04-22T10:15:00Z` | ISO-8601 UTC timestamp |
| trust_tier | TEXT | Yes | `official_filing` | Reliability label used in ranking |

## Additional Operational Fields
These are recommended to support indexing and debugging.

| Field | Type | Required | Example | Purpose |
|---|---|---|---|---|
| document_id | TEXT | Yes | `doc_tesla_2024_10k` | Stable document key |
| chunk_id | TEXT | Yes | `doc_tesla_2024_10k_p187_c03` | Stable chunk key |
| chunk_index | INTEGER | Yes | `3` | Chunk order on page/section |
| text | TEXT | Yes | `...` | Chunk body used for embedding |
| token_count | INTEGER | No | `312` | Monitoring and model fit |
| embedding_model | TEXT | Yes | `BAAI/bge-base-en-v1.5` | Traceability for re-indexing |
| embedding_dim | INTEGER | Yes | `768` | Validation at query time |

## Trust Tier Values
- `official_filing`: SEC filing or company annual report
- `official_ir`: investor relations earnings/presentation materials
- `curated_research`: manually selected external research PDF
- `external_web`: fallback web evidence

## Validation Rules
- `company`, `source_type`, `trust_tier` must be from controlled enums.
- `year` must be `>= 1990` and `<= current_year + 1`.
- `page_number` must be `>= 1`.
- `chunk_id` must be unique globally.
- `section_title` can be null when unavailable.

## Citation Payload Contract
Minimum fields returned to answer synthesizer:
- `filename`
- `company`
- `year`
- `source_type`
- `page_number`
- `section_title`
- `trust_tier`
- `chunk_id`
