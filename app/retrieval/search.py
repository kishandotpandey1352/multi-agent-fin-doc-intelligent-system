from pathlib import Path
from typing import Any, Dict, List, Optional

from app.retrieval.db import connect, fetch_chunk_by_vector_ids
from app.retrieval.embedding import EmbeddingModel
from app.retrieval.vector_store import FaissStore


TRUST_BONUS = {
    "official_filing": 0.08,
    "official_ir": 0.05,
    "curated_research": 0.02,
    "external_web": 0.0,
}


def apply_filters(
    rows: List[Dict[str, Any]],
    company: Optional[str] = None,
    year: Optional[int] = None,
    source_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filtered = []
    for row in rows:
        if company and row["company"] != company:
            continue
        if year and row["year"] != year:
            continue
        if source_type and row["source_type"] != source_type:
            continue
        filtered.append(row)
    return filtered


def rerank(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for row in rows:
        trust_bonus = TRUST_BONUS.get(row["trust_tier"], 0.0)
        recency_bonus = min(max((row["year"] - 2015) * 0.001, 0.0), 0.02)
        row["final_score"] = row["score"] + trust_bonus + recency_bonus

    rows.sort(key=lambda x: x["final_score"], reverse=True)
    return rows


def enforce_diversity(rows: List[Dict[str, Any]], final_k: int) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    per_doc_count: Dict[str, int] = {}

    for row in rows:
        doc_id = row["document_id"]
        if per_doc_count.get(doc_id, 0) >= 2:
            continue
        selected.append(row)
        per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1
        if len(selected) >= final_k:
            break

    return selected


def search(
    query: str,
    index_dir: Path = Path("data/index"),
    model_name: str = "BAAI/bge-base-en-v1.5",
    company: Optional[str] = None,
    year: Optional[int] = None,
    source_type: Optional[str] = None,
    top_k: int = 12,
    final_k: int = 8,
) -> List[Dict[str, Any]]:
    db_path = index_dir / "metadata.db"
    index_path = index_dir / "faiss.index"

    embedder = EmbeddingModel(model_name=model_name)
    store = FaissStore(index_path=index_path, dimension=embedder.dimension)
    conn = connect(db_path)

    query_vector = embedder.embed_query(query)
    effective_top_k = top_k if not any([company, year, source_type]) else max(top_k, 200)
    vector_ids, scores = store.search(query_vector=query_vector, top_k=effective_top_k)

    rows = fetch_chunk_by_vector_ids(conn, vector_ids)
    score_map = {vector_id: score for vector_id, score in zip(vector_ids, scores)}
    for row in rows:
        row["score"] = score_map.get(row["vector_id"], 0.0)

    rows = apply_filters(rows, company=company, year=year, source_type=source_type)
    rows = rerank(rows)
    rows = enforce_diversity(rows, final_k=final_k)

    conn.close()
    return rows
