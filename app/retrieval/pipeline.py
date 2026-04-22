from pathlib import Path
from typing import Dict, List, Optional, Sequence

from app.ingestion.pdf_loader import load_pdf_pages
from app.retrieval.chunking import build_chunks_for_page
from app.retrieval.db import clear_all, connect, init_schema, insert_chunk, insert_document, insert_vector_map
from app.retrieval.embedding import EmbeddingModel
from app.retrieval.metadata import build_document_metadata
from app.retrieval.vector_store import FaissStore


def discover_pdfs(data_root: Path) -> List[Path]:
    return sorted(data_root.rglob("*.pdf"))


def company_from_path(pdf_path: Path, data_root: Path) -> Optional[str]:
    rel = pdf_path.relative_to(data_root)
    parts = list(rel.parts)
    if not parts:
        return None
    if parts[0].lower() == "research":
        return "research"
    return parts[0].lower()


def estimate_token_count(text: str) -> int:
    return max(1, len(text.split()))


def build_index(
    data_root: Path = Path("data"),
    index_dir: Path = Path("data/index"),
    model_name: str = "BAAI/bge-base-en-v1.5",
    max_docs: Optional[int] = None,
    company_filters: Optional[Sequence[str]] = None,
    max_pages: Optional[int] = None,
    reset_index: bool = True,
) -> Dict[str, int]:
    db_path = index_dir / "metadata.db"
    index_path = index_dir / "faiss.index"

    embedder = EmbeddingModel(model_name=model_name)
    store = FaissStore(index_path=index_path, dimension=embedder.dimension)

    conn = connect(db_path)
    init_schema(conn)

    if reset_index:
        store.reset()
        clear_all(conn)

    pdf_paths = discover_pdfs(data_root)
    if company_filters:
        wanted = {name.lower().strip() for name in company_filters}
        pdf_paths = [
            path
            for path in pdf_paths
            if company_from_path(path, data_root) in wanted
        ]
    docs_indexed = 0
    chunks_indexed = 0
    total_vectors = 0

    for pdf_path in pdf_paths:
        if max_docs is not None and docs_indexed >= max_docs:
            break

        metadata = build_document_metadata(pdf_path=pdf_path, data_root=data_root)
        if metadata is None:
            continue

        pages = load_pdf_pages(pdf_path)
        if max_pages is not None:
            pages = pages[:max_pages]
        doc_chunks = []
        chunk_counter = 0

        for page in pages:
            page_chunks = build_chunks_for_page(
                page_number=page.page_number,
                page_text=page.text,
                start_index=chunk_counter,
            )
            doc_chunks.extend(page_chunks)
            chunk_counter += len(page_chunks)

        if not doc_chunks:
            continue

        texts = [chunk.text for chunk in doc_chunks]
        vectors = embedder.embed_texts(texts)
        start_id, end_id = store.add(vectors)

        insert_document(conn, metadata.__dict__)

        for offset, chunk in enumerate(doc_chunks):
            chunk_id = f"{metadata.document_id}_p{chunk.page_number}_c{chunk.chunk_index:03d}"
            row = {
                "chunk_id": chunk_id,
                "document_id": metadata.document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "text": chunk.text,
                "token_count": estimate_token_count(chunk.text),
                "embedding_model": embedder.model_name,
                "embedding_dim": embedder.dimension,
            }
            insert_chunk(conn, row)
            insert_vector_map(conn, vector_id=start_id + offset, chunk_id=chunk_id)

        conn.commit()
        docs_indexed += 1
        chunks_indexed += len(doc_chunks)
        total_vectors = end_id

        print(f"Indexed: {metadata.filename} ({len(doc_chunks)} chunks)")

    store.save()
    conn.close()

    return {
        "documents": docs_indexed,
        "chunks": chunks_indexed,
        "vectors": total_vectors,
    }
