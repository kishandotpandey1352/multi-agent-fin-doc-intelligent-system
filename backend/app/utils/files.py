from pathlib import Path
from typing import BinaryIO
import shutil


def save_upload_to_temp(file_obj: BinaryIO, filename: str, temp_dir: Path) -> Path:
    temp_dir.mkdir(parents=True, exist_ok=True)
    destination = temp_dir / filename
    with destination.open("wb") as handle:
        shutil.copyfileobj(file_obj, handle)
    return destination
