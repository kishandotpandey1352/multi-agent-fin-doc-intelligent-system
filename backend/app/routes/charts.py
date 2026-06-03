from fastapi import APIRouter
import logging

from backend.app.schemas.requests import AnswerRequest
from backend.app.schemas.responses import AnswerResponse
from backend.app.services.answer_service import run_answer


router = APIRouter(prefix="/charts", tags=["charts"])


@router.post("", response_model=AnswerResponse)
def chart_request(request: AnswerRequest) -> AnswerResponse:
    result = run_answer(
        question=request.question,
        company=request.company,
        year=request.year,
        source=request.source,
        intent="chart_request",
        top_k=request.top_k,
        final_k=request.final_k,
        mode=request.mode,
    )
    payload = result["answer"]
    payload["plan"] = result["plan"]
    payload["retrieval"] = result["retrieval"]
    payload["critic"] = result.get("critic")
    payload["mode"] = result.get("mode")
    payload["timings"] = result.get("timings")

    try:
        charts = payload.get("charts", []) if isinstance(payload, dict) else []
        num_charts = len(charts) if isinstance(charts, list) else 0
    except Exception:
        num_charts = 0
    logging.getLogger(__name__).info(f"chart_request: returning charts={num_charts}")

    return AnswerResponse(**payload)
