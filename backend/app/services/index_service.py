from pathlib import Path
from typing import Dict, Optional, Sequence

from app.retrieval.pipeline import build_index


def run_index(
    data_root: Path,
    index_dir: Path,
    max_docs: Optional[int],
    company_filters: Optional[Sequence[str]],
    max_pages: Optional[int],
    reset_index: bool,
) -> Dict[str, int]:
    return build_index(
        data_root=data_root,
        index_dir=index_dir,
        max_docs=max_docs,
        company_filters=company_filters,
        max_pages=max_pages,
        reset_index=reset_index,
    )
