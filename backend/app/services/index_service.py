from pathlib import Path
from typing import Dict, Optional, Sequence

from app.retrieval.pipeline import build_index
import time


def run_index(
    data_root: Path,
    index_dir: Path,
    max_docs: Optional[int],
    company_filters: Optional[Sequence[str]],
    max_pages: Optional[int],
    reset_index: bool,
) -> Dict[str, int]:
    start = time.perf_counter()
    stats = build_index(
        data_root=data_root,
        index_dir=index_dir,
        max_docs=max_docs,
        company_filters=company_filters,
        max_pages=max_pages,
        reset_index=reset_index,
    )
    stats_out = dict(stats)
    stats_out["index_time_seconds"] = round(time.perf_counter() - start, 3)
    return stats_out
