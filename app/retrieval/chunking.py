from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Chunk:
    chunk_index: int
    page_number: int
    section_title: Optional[str]
    text: str


def infer_section_title(page_text: str) -> Optional[str]:
    for line in page_text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if len(candidate) > 100:
            continue
        if candidate.isupper() or candidate.istitle():
            return candidate
        return candidate
    return None


def split_recursive(text: str, chunk_size: int, separators: List[str]) -> List[str]:
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep = separators[0]
    if sep == "":
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    parts = text.split(sep)
    if len(parts) == 1:
        return split_recursive(text, chunk_size, separators[1:])

    chunks: List[str] = []
    current = ""

    for part in parts:
        piece = part if not current else sep + part
        if len(current) + len(piece) <= chunk_size:
            current += piece
            continue

        if current.strip():
            chunks.append(current.strip())
        if len(part) > chunk_size:
            chunks.extend(split_recursive(part, chunk_size, separators[1:]))
            current = ""
        else:
            current = part

    if current.strip():
        chunks.append(current.strip())

    return chunks


def add_overlap(chunks: List[str], overlap: int) -> List[str]:
    if overlap <= 0 or not chunks:
        return chunks

    merged: List[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            merged.append(chunk)
            continue
        tail = chunks[i - 1][-overlap:]
        merged.append((tail + " " + chunk).strip())
    return merged


def chunk_page_text(page_text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
    separators = ["\n\n", "\n", ". ", " ", ""]
    base_chunks = split_recursive(page_text, chunk_size=chunk_size, separators=separators)
    return add_overlap(base_chunks, overlap=overlap)


def build_chunks_for_page(page_number: int, page_text: str, start_index: int) -> List[Chunk]:
    section_title = infer_section_title(page_text)
    chunk_texts = chunk_page_text(page_text)

    chunks: List[Chunk] = []
    idx = start_index
    for text in chunk_texts:
        clean_text = text.strip()
        if not clean_text:
            continue
        chunks.append(
            Chunk(
                chunk_index=idx,
                page_number=page_number,
                section_title=section_title,
                text=clean_text,
            )
        )
        idx += 1

    return chunks
