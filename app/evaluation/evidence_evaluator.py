from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.llm.ollama_client import get_ollama_client


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


@dataclass
class EvidenceScore:
    relevance: float
    specificity: float
    trustworthiness: float
    recency: float
    support: float
    overall: float
    justification: str


class EvidenceEvaluator:
    def __init__(self, llm: Optional[OllamaClient] = None, mode: str = "deterministic") -> None:
        self.llm = llm or (get_ollama_client() if mode != "deterministic" else None)
        self.mode = mode

    def evaluate(
        self,
        question: str,
        rows: List[Dict[str, Any]],
        max_results: Optional[int] = None,
        threshold: float = 0.45,
    ) -> Dict[str, Any]:
        llm_scores: Dict[str, EvidenceScore] = {}
        if self.llm and self.mode == "replace":
            llm_scores = self._llm_score_rows(question, rows)

        scored: List[Tuple[Dict[str, Any], EvidenceScore]] = []
        for row in rows:
            if row.get("chunk_id") in llm_scores:
                score = llm_scores[row.get("chunk_id")]
            else:
                score = self._score_row(question, row)
            scored.append((row, score))

        scored.sort(key=lambda item: item[1].overall, reverse=True)

        filtered = [item for item in scored if item[1].overall >= threshold]
        if not filtered:
            filtered = scored[: min(3, len(scored))]

        if max_results is not None:
            filtered = filtered[: max_results]

        filtered_rows: List[Dict[str, Any]] = []
        for row, score in filtered:
            enriched = dict(row)
            enriched["evidence_score"] = score.overall
            enriched["evidence_justification"] = score.justification
            enriched["evidence_breakdown"] = {
                "relevance": score.relevance,
                "specificity": score.specificity,
                "trustworthiness": score.trustworthiness,
                "recency": score.recency,
                "support": score.support,
            }
            filtered_rows.append(enriched)

        evaluation = {
            "threshold": threshold,
            "kept": len(filtered_rows),
            "dropped": max(len(rows) - len(filtered_rows), 0),
            "items": [
                {
                    "chunk_id": row.get("chunk_id"),
                    "document_id": row.get("document_id"),
                    "evidence_score": score.overall,
                    "justification": score.justification,
                }
                for row, score in filtered
            ],
        }

        if self.llm and self.mode == "augment":
            evaluation["llm_note"] = self._llm_note(question, rows[:6])

        return {
            "filtered_rows": filtered_rows,
            "evaluation": evaluation,
        }

    def _llm_score_rows(self, question: str, rows: List[Dict[str, Any]]) -> Dict[str, EvidenceScore]:
        if not rows:
            return {}
        sample = rows[:8]
        prompt = (
            "Return JSON: {\"scores\": [{\"chunk_id\":..., \"relevance\":0.0,...}]}\n"
            f"Question: {question}\nChunks: {sample}"
        )
        raw = self.llm.generate(prompt, max_tokens=256, temperature=0.0)
        try:
            result = json.loads(raw)
        except Exception:
            return {}
        scores = result.get("scores") if isinstance(result, dict) else None
        if not isinstance(scores, list):
            return {}

        output: Dict[str, EvidenceScore] = {}
        for item in scores:
            if not isinstance(item, dict):
                continue
            chunk_id = str(item.get("chunk_id", ""))
            if not chunk_id:
                continue
            score = EvidenceScore(
                relevance=float(item.get("relevance", 0.0) or 0.0),
                specificity=float(item.get("specificity", 0.0) or 0.0),
                trustworthiness=float(item.get("trustworthiness", 0.0) or 0.0),
                recency=float(item.get("recency", 0.0) or 0.0),
                support=float(item.get("support", 0.0) or 0.0),
                overall=float(item.get("overall", 0.0) or 0.0),
                justification=str(item.get("justification", "")),
            )
            output[chunk_id] = score
        return output

    def _llm_note(self, question: str, rows: List[Dict[str, Any]]) -> str:
        if not self.llm or not rows:
            return ""
        prompt = (
            "Provide a single-sentence note about evidence quality for this question.\n"
            f"Question: {question}\nChunks: {rows}"
        )
        return self.llm.generate(prompt, max_tokens=64, temperature=0.0)

    def _score_row(self, question: str, row: Dict[str, Any]) -> EvidenceScore:
        relevance = self._relevance(row, question)
        specificity = self._specificity(row)
        trustworthiness = self._trustworthiness(row)
        recency = self._recency(row)
        support = self._support(question, row)

        overall = (
            relevance * 0.35
            + support * 0.25
            + trustworthiness * 0.2
            + recency * 0.1
            + specificity * 0.1
        )
        overall = round(min(max(overall, 0.0), 1.0), 3)

        justification = (
            "rel={rel:.2f}, spec={spec:.2f}, trust={trust:.2f}, "
            "recency={recency:.2f}, support={support:.2f}, overall={overall:.2f}"
        ).format(
            rel=relevance,
            spec=specificity,
            trust=trustworthiness,
            recency=recency,
            support=support,
            overall=overall,
        )

        return EvidenceScore(
            relevance=relevance,
            specificity=specificity,
            trustworthiness=trustworthiness,
            recency=recency,
            support=support,
            overall=overall,
            justification=justification,
        )

    def _relevance(self, row: Dict[str, Any], question: str) -> float:
        base = row.get("final_score", row.get("score", 0.0))
        try:
            numeric = float(base)
        except (TypeError, ValueError):
            numeric = 0.0

        if numeric > 0:
            return min(max(numeric, 0.0), 1.0)

        overlap = self._token_overlap(question, str(row.get("text", "")))
        return overlap

    def _specificity(self, row: Dict[str, Any]) -> float:
        text = str(row.get("text", ""))
        tokens = [token for token in text.split() if token]
        if not tokens:
            return 0.0

        numeric = sum(1 for token in tokens if any(char.isdigit() for char in token))
        caps = sum(1 for token in tokens if token.isupper() and len(token) > 2)
        richness = min((numeric + caps) / 12.0, 1.0)
        length_boost = min(len(tokens) / 120.0, 1.0) * 0.3
        return round(min(richness + length_boost, 1.0), 3)

    def _trustworthiness(self, row: Dict[str, Any]) -> float:
        trust_tier = str(row.get("trust_tier", "")).lower()
        source_type = str(row.get("source_type", "")).lower()

        if "internal" in trust_tier:
            return 0.9
        if trust_tier in {"official_filing", "official_ir"}:
            return 0.85
        if trust_tier == "regulator_gov":
            return 0.9
        if trust_tier == "reputable_news":
            return 0.65
        if trust_tier == "unknown_blog":
            return 0.3
        if "external" in trust_tier or source_type == "web":
            return 0.4

        if source_type in {"annual", "earnings", "presentations"}:
            return 0.85

        filename = str(row.get("filename", "")).lower()
        if "sec" in filename or "10-k" in filename or "10k" in filename:
            return 0.85

        return 0.6

    def _recency(self, row: Dict[str, Any]) -> float:
        year = row.get("year")
        try:
            year_value = int(year)
        except (TypeError, ValueError):
            return 0.5

        if year_value <= 0:
            return 0.5

        current = datetime.utcnow().year
        delta = max(current - year_value, 0)
        score = 1.0 - min(delta / 10.0, 1.0)
        return round(max(score, 0.0), 3)

    def _support(self, question: str, row: Dict[str, Any]) -> float:
        return self._token_overlap(question, str(row.get("text", "")))

    def _token_overlap(self, question: str, text: str) -> float:
        question_tokens = self._keyword_tokens(question)
        if not question_tokens:
            return 0.0

        text_tokens = set(self._keyword_tokens(text))
        overlap = len([token for token in question_tokens if token in text_tokens])
        return round(overlap / max(len(question_tokens), 1), 3)

    def _keyword_tokens(self, text: str) -> List[str]:
        tokens = [token.strip(".,;:()[]{}\"'\n\t").lower() for token in text.split()]
        return [token for token in tokens if token and token not in _STOPWORDS]
