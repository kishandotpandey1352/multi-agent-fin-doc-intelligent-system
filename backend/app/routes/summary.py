from fastapi import APIRouter

from backend.app.schemas.requests import AnswerRequest
from backend.app.schemas.responses import AnswerResponse
from backend.app.services.answer_service import run_answer


router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("", response_model=AnswerResponse)
def summarize(request: AnswerRequest) -> AnswerResponse:
    result = run_answer(
        question=request.question,
        company=request.company,
        year=request.year,
        source=request.source,
        intent="summary",
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
    return AnswerResponse(**payload)
