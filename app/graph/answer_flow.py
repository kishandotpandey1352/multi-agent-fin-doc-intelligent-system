from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.planner import Planner
from app.agents.synthesizer import Synthesizer
from app.retrieval.retriever import RetrievalRequest, Retriever


class AnswerState(TypedDict, total=False):
    query: str
    company: Optional[str]
    year: Optional[int]
    plan: Dict[str, Any]
    retrieval: Dict[str, Any]
    retrieved_rows: List[Dict[str, Any]]
    answer: Dict[str, Any]


def build_answer_graph() -> Any:
    planner = Planner()
    retriever = Retriever()
    synthesizer = Synthesizer()

    def plan_node(state: AnswerState) -> AnswerState:
        plan_obj = planner.plan(
            query=state["query"],
            company=state.get("company"),
            year=state.get("year"),
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
        )
        retrieval = retriever.retrieve(request)
        return {
            "retrieval": retrieval,
            "retrieved_rows": retrieval.get("results", []),
        }

    def synthesize_node(state: AnswerState) -> AnswerState:
        plan = state["plan"]
        answer = synthesizer.synthesize(
            query=state["query"],
            intent=str(plan["intent"]),
            retrieved_rows=state.get("retrieved_rows", []),
        )
        return {"answer": answer}

    graph = StateGraph(AnswerState)
    graph.add_node("plan_step", plan_node)
    graph.add_node("retrieve_step", retrieve_node)
    graph.add_node("synthesize_step", synthesize_node)

    graph.set_entry_point("plan_step")
    graph.add_edge("plan_step", "retrieve_step")
    graph.add_edge("retrieve_step", "synthesize_step")
    graph.add_edge("synthesize_step", END)

    return graph.compile()


def run_answer_pipeline(query: str, company: Optional[str] = None, year: Optional[int] = None) -> AnswerState:
    app = build_answer_graph()
    initial_state: AnswerState = {
        "query": query,
        "company": company,
        "year": year,
    }
    return app.invoke(initial_state)
