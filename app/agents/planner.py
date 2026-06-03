from dataclasses import dataclass
from typing import Dict, Optional

from app.llm.ollama_client import get_ollama_client
import json


PLAN_QA = "qa"
PLAN_SUMMARY = "summary"
PLAN_CHART = "chart_request"
PLAN_COMPARATIVE = "comparative_analysis"


@dataclass
class QueryPlan:
    intent: str
    rewritten_query: str
    retrieve_source: str = "auto"
    company: Optional[str] = None
    year: Optional[int] = None
    source_type: Optional[str] = None
    top_k: int = 12
    final_k: int = 8
    llm_plan: Optional[Dict[str, object]] = None


class Planner:
    def __init__(self, llm: Optional[object] = None, mode: str = "deterministic") -> None:
        self.mode = mode
        self.llm = llm or (get_ollama_client() if mode != "deterministic" else None)

    def classify(self, query: str) -> str:
        lowered = query.lower()

        chart_terms = (
            "chart",
            "plot",
            "graph",
            "visual",
            "trend line",
            "time series",
        )
        compare_terms = (
            "compare",
            "comparison",
            "versus",
            "vs",
            "relative to",
            "better than",
        )
        summary_terms = (
            "summarize",
            "summary",
            "overview",
            "high level",
            "recap",
        )

        if any(term in lowered for term in chart_terms):
            return PLAN_CHART
        if any(term in lowered for term in compare_terms):
            return PLAN_COMPARATIVE
        if any(term in lowered for term in summary_terms):
            return PLAN_SUMMARY
        return PLAN_QA

    def plan(self, query: str, company: Optional[str] = None, year: Optional[int] = None, mode: str = "deterministic") -> QueryPlan:
        
        intent = self.classify(query)

        rewritten_query = query.strip()
        # optionally use LLM to rewrite or augment the query
        if mode and mode != "deterministic":
            client = get_ollama_client()
            prompt = f"Rewrite this query for retrieval succinctly: {rewritten_query}\nProvide a single-line concise rewrite." 
            suggestion = client.generate(prompt, max_tokens=64, temperature=0.0).strip()
            if suggestion:
                if mode == "augment":
                    rewritten_query = f"{rewritten_query} | {suggestion}"
                else:
                    rewritten_query = suggestion
        if intent == PLAN_SUMMARY and "summary" not in rewritten_query.lower():
            rewritten_query = f"Summary request: {rewritten_query}"
        elif intent == PLAN_CHART and "trend" not in rewritten_query.lower():
            rewritten_query = f"Time-series evidence request: {rewritten_query}"
        elif intent == PLAN_COMPARATIVE and "compare" not in rewritten_query.lower():
            rewritten_query = f"Comparative analysis request: {rewritten_query}"

        final_k = 10 if intent in (PLAN_SUMMARY, PLAN_COMPARATIVE) else 8

        plan = QueryPlan(
            intent=intent,
            rewritten_query=rewritten_query,
            retrieve_source="auto",
            company=company,
            year=year,
            source_type=None,
            top_k=14,
            final_k=final_k,
        )

        llm_plan = self._llm_plan(query=query, company=company, year=year)
        if llm_plan and self.mode == "replace":
            plan.intent = str(llm_plan.get("intent", plan.intent))
            plan.rewritten_query = str(llm_plan.get("rewritten_query", plan.rewritten_query))
            plan.retrieve_source = str(llm_plan.get("retrieve_source", plan.retrieve_source))
            plan.top_k = int(llm_plan.get("top_k", plan.top_k))
            plan.final_k = int(llm_plan.get("final_k", plan.final_k))
        elif llm_plan and self.mode == "augment":
            plan.llm_plan = llm_plan

        return plan

    def to_dict(self, plan: QueryPlan) -> Dict[str, object]:
        payload = {
            "intent": plan.intent,
            "rewritten_query": plan.rewritten_query,
            "retrieve_source": plan.retrieve_source,
            "company": plan.company,
            "year": plan.year,
            "source_type": plan.source_type,
            "top_k": plan.top_k,
            "final_k": plan.final_k,
        }
        if plan.llm_plan:
            payload["llm_plan"] = plan.llm_plan
        return payload

    def _llm_plan(
        self,
        query: str,
        company: Optional[str],
        year: Optional[int],
    ) -> Optional[Dict[str, object]]:
        if not self.llm or self.mode == "deterministic":
            return None

        prompt = (
            "Return JSON with keys: intent, rewritten_query, retrieve_source, top_k, final_k.\n"
            f"Question: {query}\nCompany: {company or ''}\nYear: {year or ''}"
        )
        raw = self.llm.generate(prompt, max_tokens=128, temperature=0.0)
        try:
            result = json.loads(raw)
        except Exception:
            return None
        if not isinstance(result, dict):
            return None
        if "intent" not in result or "rewritten_query" not in result:
            return None
        return result
