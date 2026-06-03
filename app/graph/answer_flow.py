from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.planner import Planner
from app.agents.critic import Critic
from app.agents.synthesizer import Synthesizer
from app.evaluation.evidence_evaluator import EvidenceEvaluator
from app.retrieval.retriever import RetrievalRequest, Retriever
from app.llm.ollama_client import get_ollama_client


class AnswerState(TypedDict, total=False):
    query: str
    company: Optional[str]
    year: Optional[int]
    mode: str
    retry_count: int
    max_retries: int
    plan: Dict[str, Any]
    retrieval: Dict[str, Any]
    retrieved_rows: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    answer: Dict[str, Any]
    critic: Dict[str, Any]


def build_answer_graph(mode: str = "deterministic") -> Any:
    llm = get_ollama_client()
    planner = Planner(llm=llm, mode=mode)
    retriever = Retriever(llm=llm, mode=mode)
    evaluator = EvidenceEvaluator(llm=llm, mode=mode)
    synthesizer = Synthesizer(llm=llm, mode=mode)
    critic = Critic(llm=llm, mode=mode)

    def plan_node(state: AnswerState) -> AnswerState:
        plan_obj = planner.plan(
            query=state["query"],
            company=state.get("company"),
            year=state.get("year"),
            mode=str(state.get("mode", mode)),
        )
        return {"plan": planner.to_dict(plan_obj)}

    def retrieve_node(state: AnswerState) -> AnswerState:
        plan = state["plan"]
        request = RetrievalRequest(
            question=str(plan["rewritten_query"]),
            company=plan.get("company"),
            year=plan.get("year"),
            source_type=plan.get("source_type"),
            top_k=int(plan.get("top_k", 12)),
            final_k=int(plan.get("final_k", 8)),
            source=str(plan.get("retrieve_source", "auto")),
            mode=str(state.get("mode", mode)),
        )
        retrieval = retriever.retrieve(request)
        return {
            "retrieval": retrieval,
            "retrieved_rows": retrieval.get("results", []),
        }

    def evaluate_node(state: AnswerState) -> AnswerState:
        plan = state["plan"]
        evaluation = evaluator.evaluate(
            question=str(plan.get("rewritten_query", state["query"])),
            rows=state.get("retrieved_rows", []),
            max_results=int(plan.get("final_k", 8)),
        )
        retrieval = dict(state.get("retrieval", {}))
        retrieval["evaluation"] = evaluation["evaluation"]
        return {
            "retrieval": retrieval,
            "retrieved_rows": evaluation["filtered_rows"],
            "evaluation": evaluation["evaluation"],
        }

    def synthesize_node(state: AnswerState) -> AnswerState:
        plan = state["plan"]
        answer = synthesizer.synthesize(
            query=state["query"],
            intent=str(plan["intent"]),
            retrieved_rows=state.get("retrieved_rows", []),
        )
        return {"answer": answer}

    def critic_node(state: AnswerState) -> AnswerState:
        report = critic.review(
            question=state["query"],
            answer=state.get("answer", {}),
            retrieved_rows=state.get("retrieved_rows", []),
        )
        answer = dict(state.get("answer", {}))
        critic_confidence = report.get("confidence_score")
        if critic_confidence is not None:
            answer["confidence_score"] = min(
                float(answer.get("confidence_score", 0.0) or 0.0),
                float(critic_confidence),
            )
        if report.get("reduce_confidence"):
            note = str(answer.get("confidence_note", "")).strip()
            summary = str(report.get("summary", "")).strip()
            if summary:
                answer["confidence_note"] = f"{note} Critic: {summary}".strip()
        return {"critic": report, "answer": answer}

    def retry_node(state: AnswerState) -> AnswerState:
        plan = dict(state.get("plan", {}))
        retry_count = int(state.get("retry_count", 0)) + 1
        top_k = int(plan.get("top_k", 12)) + 4
        final_k = int(plan.get("final_k", 8)) + 2
        plan["top_k"] = min(top_k, 30)
        plan["final_k"] = min(final_k, 15)

        source = str(plan.get("retrieve_source", "auto"))
        if retry_count >= 2 and source == "auto":
            plan["retrieve_source"] = "web"

        return {
            "plan": plan,
            "retry_count": retry_count,
        }

    def should_retry(state: AnswerState) -> str:
        report = state.get("critic", {})
        retry_count = int(state.get("retry_count", 0))
        max_retries = int(state.get("max_retries", 2))
        if report.get("should_retry") and retry_count < max_retries:
            return "retry"
        return "end"

    graph = StateGraph(AnswerState)
    graph.add_node("plan_step", plan_node)
    graph.add_node("retrieve_step", retrieve_node)
    graph.add_node("evaluate_step", evaluate_node)
    graph.add_node("synthesize_step", synthesize_node)
    graph.add_node("critic_step", critic_node)
    graph.add_node("retry_step", retry_node)

    graph.set_entry_point("plan_step")
    graph.add_edge("plan_step", "retrieve_step")
    graph.add_edge("retrieve_step", "evaluate_step")
    graph.add_edge("evaluate_step", "synthesize_step")
    graph.add_edge("synthesize_step", "critic_step")
    graph.add_conditional_edges(
        "critic_step",
        should_retry,
        {
            "retry": "retry_step",
            "end": END,
        },
    )
    graph.add_edge("retry_step", "retrieve_step")

    return graph.compile()


def run_answer_pipeline(
    query: str,
    company: Optional[str] = None,
    year: Optional[int] = None,
    mode: str = "deterministic",
) -> AnswerState:
    app = build_answer_graph(mode=mode)
    initial_state: AnswerState = {
        "query": query,
        "company": company,
        "year": year,
        "mode": mode,
        "retry_count": 0,
        "max_retries": 2,
    }
    return app.invoke(initial_state)
