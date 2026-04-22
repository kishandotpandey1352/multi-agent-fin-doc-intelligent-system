from pathlib import Path
import shutil


VALID_COMPANIES = {"tesla", "apple", "nvidia", "research"}
VALID_SOURCE_TYPES = {"annual", "earnings", "presentations", "research"}


def stage_uploaded_pdf(
    file_path: Path,
    company: str,
    source_type: str,
    data_root: Path = Path("data"),
) -> Path:
    company = company.lower().strip()
    source_type = source_type.lower().strip()

    if company not in VALID_COMPANIES:
        raise ValueError(f"Unsupported company: {company}")
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError(f"Unsupported source_type: {source_type}")
    if not file_path.exists() or file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Input PDF not found: {file_path}")

    if company == "research" or source_type == "research":
        destination_dir = data_root / "research"
    else:
        destination_dir = data_root / company / source_type

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / file_path.name
    shutil.copy2(file_path, destination)
    return destination
