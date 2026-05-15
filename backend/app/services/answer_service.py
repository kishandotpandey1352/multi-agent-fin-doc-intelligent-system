from typing import Any, Dict, Optional

from app.agents.planner import Planner
from app.agents.synthesizer import Synthesizer
from app.retrieval.retriever import RetrievalRequest, Retriever


INTENT_PREFIX = {
    "summary": "Summarize: ",
    "chart_request": "Create a chart: ",
    "comparative_analysis": "Compare: ",
}


def run_answer(
    question: str,
    company: Optional[str],
    year: Optional[int],
    source: Optional[str],
    intent: Optional[str],
    top_k: Optional[int],
    final_k: Optional[int],
) -> Dict[str, Any]:
    planner = Planner()
    retriever = Retriever()
    synthesizer = Synthesizer()

    plan = planner.plan(query=question, company=company, year=year)

    if intent:
        normalized_intent = intent.strip().lower()
        if normalized_intent in INTENT_PREFIX and not question.lower().startswith(INTENT_PREFIX[normalized_intent].lower()):
            question = INTENT_PREFIX[normalized_intent] + question
        plan.intent = normalized_intent
        plan.rewritten_query = question

    if top_k is not None:
        plan.top_k = top_k
    if final_k is not None:
        plan.final_k = final_k
    if source:
        plan.retrieve_source = source

    request = RetrievalRequest(
        question=str(plan.rewritten_query),
        company=plan.company,
        year=plan.year,
        source_type=plan.source_type,
        top_k=int(plan.top_k),
        final_k=int(plan.final_k),
        source=str(plan.retrieve_source),
    )
    retrieval = retriever.retrieve(request)
    answer = synthesizer.synthesize(
        query=question,
        intent=str(plan.intent),
        retrieved_rows=retrieval.get("results", []),
    )

    return {
        "answer": answer,
        "plan": planner.to_dict(plan),
        "retrieval": retrieval,
    }
