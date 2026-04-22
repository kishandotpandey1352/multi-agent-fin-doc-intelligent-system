# Day 3 Model and Store Decisions (Final)

## Embedding Model
Decision: `BAAI/bge-base-en-v1.5`

Rationale:
- Open-source and production-proven for semantic retrieval.
- Good quality/latency tradeoff for local experimentation.
- 768-dim vectors keep memory and index size manageable.

Implementation notes:
- Normalize vectors before indexing to support cosine similarity.
- Persist model name and dimension in metadata for compatibility checks.

## Vector Store
Decision: FAISS

Rationale:
- Already aligned with project architecture.
- Fast local similarity search and simple operations.
- No external service dependency for early milestones.

Initial index strategy:
- Use `IndexFlatIP` with normalized embeddings (cosine equivalent).
- Move to IVF/HNSW variants only after corpus growth justifies it.

## Metadata/App Database
Decision: SQLite first, Postgres later

Rationale:
- SQLite is lightweight and ideal for early-stage development.
- Easy local setup and reproducibility.
- Postgres migration path is clear once concurrency and scale increase.

SQLite stores:
- document registry
- chunk metadata
- retrieval logs and evaluation signals

## Migration Trigger to Postgres
Move when one or more conditions hold:
- concurrent users exceed local write comfort
- dataset and metadata operations become latency-bound
- need stronger operational controls (roles, backup, managed hosting)

## Final Decision Summary
- Embedding model: `BAAI/bge-base-en-v1.5`
- Vector store: `FAISS`
- App DB: `SQLite` now, `Postgres` later
