CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    company TEXT NOT NULL,
    year INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    upload_time TEXT NOT NULL,
    trust_tier TEXT NOT NULL,
    path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    section_title TEXT,
    text TEXT NOT NULL,
    token_count INTEGER,
    embedding_model TEXT NOT NULL,
    embedding_dim INTEGER NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS vector_map (
    vector_id INTEGER PRIMARY KEY,
    chunk_id TEXT UNIQUE NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);
