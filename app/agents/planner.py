from dataclasses import dataclass
from typing import Dict, Optional


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


class Planner:
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

    def plan(self, query: str, company: Optional[str] = None, year: Optional[int] = None) -> QueryPlan:
        intent = self.classify(query)

        rewritten_query = query.strip()
        if intent == PLAN_SUMMARY and "summary" not in rewritten_query.lower():
            rewritten_query = f"Summary request: {rewritten_query}"
        elif intent == PLAN_CHART and "trend" not in rewritten_query.lower():
            rewritten_query = f"Time-series evidence request: {rewritten_query}"
        elif intent == PLAN_COMPARATIVE and "compare" not in rewritten_query.lower():
            rewritten_query = f"Comparative analysis request: {rewritten_query}"

        final_k = 10 if intent in (PLAN_SUMMARY, PLAN_COMPARATIVE) else 8

        return QueryPlan(
            intent=intent,
            rewritten_query=rewritten_query,
            retrieve_source="auto",
            company=company,
            year=year,
            source_type=None,
            top_k=14,
            final_k=final_k,
        )

    def to_dict(self, plan: QueryPlan) -> Dict[str, object]:
        return {
            "intent": plan.intent,
            "rewritten_query": plan.rewritten_query,
            "retrieve_source": plan.retrieve_source,
            "company": plan.company,
            "year": plan.year,
            "source_type": plan.source_type,
            "top_k": plan.top_k,
            "final_k": plan.final_k,
        }
