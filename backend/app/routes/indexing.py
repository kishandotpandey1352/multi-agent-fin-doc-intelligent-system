from pathlib import Path
from fastapi import APIRouter

from backend.app.schemas.requests import IndexRequest
from backend.app.schemas.responses import IndexResponse
from backend.app.services.index_service import run_index


router = APIRouter(prefix="/index", tags=["index"])


@router.post("/start", response_model=IndexResponse)
def start_index(request: IndexRequest) -> IndexResponse:
    stats = run_index(
        data_root=Path("data"),
        index_dir=Path("data/index"),
        max_docs=request.max_docs,
        company_filters=request.company_filters,
        max_pages=request.max_pages,
        reset_index=request.reset_index,
    )
    return IndexResponse(**stats)
