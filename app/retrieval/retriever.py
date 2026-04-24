from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.retrieval.search import search


@dataclass
class RetrievalRequest:
    question: str
    company: Optional[str] = None
    year: Optional[int] = None
    source_type: Optional[str] = None
    top_k: int = 12
    final_k: int = 8
    source: str = "auto"  # auto | local | web


class Retriever:
    def rewrite_question(self, question: str) -> str:
        text = question.strip()
        replacements = {
            "10k": "10-K annual report",
            "10-k": "10-K annual report",
            "qoq": "quarter-over-quarter",
            "yoy": "year-over-year",
            "md&a": "management discussion and analysis",
        }
        lowered = text.lower()
        for key, value in replacements.items():
            if key in lowered:
                lowered = lowered.replace(key, value)
        return lowered

    def retrieve_local(self, request: RetrievalRequest) -> Dict[str, Any]:
        rewritten = self.rewrite_question(request.question)
        rows = search(
            query=rewritten,
            company=request.company,
            year=request.year,
            source_type=request.source_type,
            top_k=request.top_k,
            final_k=request.final_k,
        )
        return {
            "source": "local",
            "query": request.question,
            "rewritten_query": rewritten,
            "results": rows,
        }

    def retrieve_web(self, request: RetrievalRequest) -> Dict[str, Any]:
        # Day 6 scope: reserve API shape for web retrieval without implementing external calls yet.
        return {
            "source": "web",
            "query": request.question,
            "rewritten_query": self.rewrite_question(request.question),
            "results": [],
            "note": "Web retrieval not implemented yet. Planned as next step.",
        }

    def retrieve(self, request: RetrievalRequest) -> Dict[str, Any]:
        if request.source == "local":
            return self.retrieve_local(request)
        if request.source == "web":
            return self.retrieve_web(request)

        local = self.retrieve_local(request)
        if local["results"]:
            return local
        return self.retrieve_web(request)
