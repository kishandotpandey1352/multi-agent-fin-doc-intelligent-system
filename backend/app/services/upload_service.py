from pathlib import Path

from app.ingestion.upload import stage_uploaded_pdf


def upload_pdf(file_path: Path, company: str, source_type: str) -> Path:
    return stage_uploaded_pdf(file_path=file_path, company=company, source_type=source_type)
