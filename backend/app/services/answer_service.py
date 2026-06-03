from typing import Any, Dict, Optional
import time
import logging

from app.agents.critic import Critic
from app.agents.planner import Planner
from app.agents.synthesizer import Synthesizer
from app.evaluation.evidence_evaluator import EvidenceEvaluator
from app.retrieval.retriever import RetrievalRequest, Retriever
from app.llm.ollama_client import get_ollama_client


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
    mode: Optional[str],
) -> Dict[str, Any]:
    llm_mode = (mode or "deterministic").strip().lower()
    llm = get_ollama_client()
    planner = Planner(llm=llm, mode=llm_mode)
    retriever = Retriever(llm=llm, mode=llm_mode)
    evaluator = EvidenceEvaluator(llm=llm, mode=llm_mode)
    synthesizer = Synthesizer(llm=llm, mode=llm_mode)
    critic = Critic(llm=llm, mode=llm_mode)

    plan = planner.plan(query=question, company=company, year=year, mode=llm_mode)

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

    max_retries = 2
    attempt = 0
    retrieval: Dict[str, Any] = {}
    answer: Dict[str, Any] = {}
    critic_report: Dict[str, Any] = {}
    # timing accumulators
    retrieval_time = 0.0
    evaluation_time = 0.0
    synthesis_time = 0.0
    critic_time = 0.0
    total_start = time.perf_counter()

    while attempt <= max_retries:
        # retrieval
        t0 = time.perf_counter()
        request = RetrievalRequest(
            question=str(plan.rewritten_query),
            company=plan.company,
            year=plan.year,
            source_type=plan.source_type,
            top_k=int(plan.top_k),
            final_k=int(plan.final_k),
            source=str(plan.retrieve_source),
            mode=llm_mode,
        )
        retrieval = retriever.retrieve(request)
        retrieval_time += time.perf_counter() - t0
        # evaluation
        t1 = time.perf_counter()
        evaluation = evaluator.evaluate(
            question=str(plan.rewritten_query),
            rows=retrieval.get("results", []),
            max_results=int(plan.final_k),
        )
        evaluation_time += time.perf_counter() - t1
        retrieval["evaluation"] = evaluation["evaluation"]
        retrieval["retry_count"] = attempt
        # synthesis
        t2 = time.perf_counter()
        answer = synthesizer.synthesize(
            query=question,
            intent=str(plan.intent),
            retrieved_rows=evaluation["filtered_rows"],
        )
        synthesis_time += time.perf_counter() - t2
        # critic
        t3 = time.perf_counter()
        critic_report = critic.review(
            question=question,
            answer=answer,
            retrieved_rows=evaluation["filtered_rows"],
        )
        critic_time += time.perf_counter() - t3

        critic_confidence = critic_report.get("confidence_score")
        if critic_confidence is not None:
            answer["confidence_score"] = min(
                float(answer.get("confidence_score", 0.0) or 0.0),
                float(critic_confidence),
            )
        if critic_report.get("reduce_confidence"):
            suggested = float(critic_report.get("suggested_confidence", 0.0) or 0.0)
            answer["confidence_score"] = min(answer.get("confidence_score", 0.0), suggested)
            note = str(answer.get("confidence_note", "")).strip()
            summary = str(critic_report.get("summary", "")).strip()
            if summary:
                answer["confidence_note"] = f"{note} Critic: {summary}".strip()

        if not critic_report.get("should_retry") or attempt >= max_retries:
            break

        attempt += 1
        plan.top_k = min(int(plan.top_k) + 4, 30)
        plan.final_k = min(int(plan.final_k) + 2, 15)
        if attempt >= 2 and plan.retrieve_source == "auto":
            plan.retrieve_source = "web"

    # log retrieval and chart counts to aid debugging (shows up in server logs)
    try:
        num_results = len(retrieval.get("results", [])) if isinstance(retrieval, dict) else 0
    except Exception:
        num_results = 0
    try:
        num_filtered = len(evaluation.get("filtered_rows", [])) if isinstance(evaluation, dict) else 0
    except Exception:
        num_filtered = 0
    try:
        num_charts = len(answer.get("charts", [])) if isinstance(answer.get("charts", []), list) else 0
    except Exception:
        num_charts = 0
    logging.getLogger(__name__).info(
        f"run_answer: retrieval_results={num_results} filtered_rows={num_filtered} charts={num_charts}"
    )

    return {
        "answer": answer,
        "plan": planner.to_dict(plan),
        "retrieval": retrieval,
        "critic": critic_report,
        "mode": llm_mode,
        "timings": {
            "retrieval_seconds": round(retrieval_time, 3),
            "evaluation_seconds": round(evaluation_time, 3),
            "synthesis_seconds": round(synthesis_time, 3),
            "critic_seconds": round(critic_time, 3),
            "total_seconds": round(time.perf_counter() - total_start, 3),
        },
    }
