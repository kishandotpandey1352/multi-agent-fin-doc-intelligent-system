from typing import Any, Dict, Optional

from app.agents.critic import Critic
from app.agents.planner import Planner
from app.agents.synthesizer import Synthesizer
from app.evaluation.evidence_evaluator import EvidenceEvaluator
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
    evaluator = EvidenceEvaluator()
    synthesizer = Synthesizer()
    critic = Critic()

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
    evaluation = evaluator.evaluate(
        question=str(plan.rewritten_query),
        rows=retrieval.get("results", []),
        max_results=int(plan.final_k),
    )
    retrieval["evaluation"] = evaluation["evaluation"]
    answer = synthesizer.synthesize(
        query=question,
        intent=str(plan.intent),
        retrieved_rows=evaluation["filtered_rows"],
    )
    critic_report = critic.review(question=question, answer=answer)
    if critic_report.get("reduce_confidence"):
        suggested = float(critic_report.get("suggested_confidence", 0.0) or 0.0)
        answer["confidence_score"] = min(answer.get("confidence_score", 0.0), suggested)
        note = str(answer.get("confidence_note", ""))
        answer["confidence_note"] = f"{note} Critic: {critic_report.get('summary', '')}".strip()

    return {
        "answer": answer,
        "plan": planner.to_dict(plan),
        "retrieval": retrieval,
        "critic": critic_report,
    }
