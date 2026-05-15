from fastapi import APIRouter

from backend.app.schemas.requests import AnswerRequest
from backend.app.schemas.responses import AnswerResponse
from backend.app.services.answer_service import run_answer


router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("", response_model=AnswerResponse)
def answer_question(request: AnswerRequest) -> AnswerResponse:
    result = run_answer(
        question=request.question,
        company=request.company,
        year=request.year,
        source=request.source,
        intent=request.intent or "qa",
        top_k=request.top_k,
        final_k=request.final_k,
    )
    payload = result["answer"]
    payload["plan"] = result["plan"]
    payload["retrieval"] = result["retrieval"]
    return AnswerResponse(**payload)
