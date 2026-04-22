from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Optional


COMPANIES = {"tesla", "apple", "nvidia", "research"}
SOURCE_TYPES = {"annual", "earnings", "presentations", "research"}


@dataclass
class DocumentMetadata:
    document_id: str
    filename: str
    company: str
    year: int
    source_type: str
    upload_time: str
    trust_tier: str
    path: str


def infer_year(filename: str, fallback_year: int) -> int:
    match = re.search(r"(19|20)\d{2}", filename)
    if match:
        return int(match.group(0))
    return fallback_year


def infer_trust_tier(source_type: str) -> str:
    if source_type == "annual":
        return "official_filing"
    if source_type in {"earnings", "presentations"}:
        return "official_ir"
    return "curated_research"


def build_document_metadata(pdf_path: Path, data_root: Path) -> Optional[DocumentMetadata]:
    rel = pdf_path.relative_to(data_root)
    parts = list(rel.parts)

    if len(parts) < 2:
        return None

    if parts[0] == "research":
        company = "research"
        source_type = "research"
    else:
        if len(parts) < 3:
            return None
        company = parts[0].lower()
        source_type = parts[1].lower()

    if company not in COMPANIES or source_type not in SOURCE_TYPES:
        return None

    filename = pdf_path.name
    year = infer_year(filename, datetime.now(timezone.utc).year)
    upload_time = datetime.now(timezone.utc).isoformat()
    trust_tier = infer_trust_tier(source_type)

    stem = pdf_path.stem.lower().replace(" ", "_")
    stem = re.sub(r"[^a-z0-9_]+", "_", stem)
    document_id = f"doc_{company}_{year}_{stem}"

    return DocumentMetadata(
        document_id=document_id,
        filename=filename,
        company=company,
        year=year,
        source_type=source_type,
        upload_time=upload_time,
        trust_tier=trust_tier,
        path=str(pdf_path),
    )
