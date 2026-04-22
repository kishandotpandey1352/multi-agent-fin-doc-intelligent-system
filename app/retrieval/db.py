import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
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
        """
    )
    conn.commit()


def clear_all(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM vector_map")
    conn.execute("DELETE FROM chunks")
    conn.execute("DELETE FROM documents")
    conn.commit()


def insert_document(conn: sqlite3.Connection, doc: Dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO documents (
            document_id, filename, company, year, source_type,
            upload_time, trust_tier, path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc["document_id"],
            doc["filename"],
            doc["company"],
            doc["year"],
            doc["source_type"],
            doc["upload_time"],
            doc["trust_tier"],
            doc["path"],
        ),
    )


def insert_chunk(conn: sqlite3.Connection, chunk: Dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO chunks (
            chunk_id, document_id, chunk_index, page_number, section_title,
            text, token_count, embedding_model, embedding_dim
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            chunk["chunk_id"],
            chunk["document_id"],
            chunk["chunk_index"],
            chunk["page_number"],
            chunk["section_title"],
            chunk["text"],
            chunk["token_count"],
            chunk["embedding_model"],
            chunk["embedding_dim"],
        ),
    )


def insert_vector_map(conn: sqlite3.Connection, vector_id: int, chunk_id: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO vector_map (vector_id, chunk_id) VALUES (?, ?)",
        (vector_id, chunk_id),
    )


def fetch_chunk_by_vector_ids(conn: sqlite3.Connection, vector_ids: List[int]) -> List[Dict[str, Any]]:
    if not vector_ids:
        return []

    placeholders = ",".join("?" for _ in vector_ids)
    rows = conn.execute(
        f"""
        SELECT
            vm.vector_id,
            c.chunk_id,
            c.document_id,
            c.chunk_index,
            c.page_number,
            c.section_title,
            c.text,
            c.token_count,
            c.embedding_model,
            c.embedding_dim,
            d.filename,
            d.company,
            d.year,
            d.source_type,
            d.upload_time,
            d.trust_tier,
            d.path
        FROM vector_map vm
        JOIN chunks c ON vm.chunk_id = c.chunk_id
        JOIN documents d ON c.document_id = d.document_id
        WHERE vm.vector_id IN ({placeholders})
        """,
        vector_ids,
    ).fetchall()

    return [dict(row) for row in rows]


def fetch_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return {"documents": doc_count, "chunks": chunk_count}
