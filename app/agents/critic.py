from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


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
class CriticReport:
    answered_coverage: float
    missing_aspects: List[str]
    citations_present: bool
    unsupported_findings: List[str]
    unsupported_risks: List[str]
    evidence_strength: float
    source_quality: float
    contradiction_level: float
    confidence_score: float
    reduce_confidence: bool
    suggested_confidence: float
    should_retry: bool
    retry_reasons: List[str]
    summary: str


class Critic:
    def review(
        self,
        question: str,
        answer: Dict[str, Any],
        retrieved_rows: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        findings = list(answer.get("findings", []))
        risks = list(answer.get("risks", []))
        citations = list(answer.get("citations", []))
        rows = retrieved_rows or []

        coverage = self._coverage_ratio(question, findings, risks)
        missing_aspects = self._missing_aspects(question, findings, risks)
        evidence_strength, source_quality = self._evidence_quality(rows)
        contradiction_level = self._contradiction_level(findings, risks)
        confidence_score = self._confidence_score(
            evidence_strength=evidence_strength,
            source_quality=source_quality,
            completeness=coverage,
            contradiction_level=contradiction_level,
        )

        citations_present = bool(citations)
        unsupported_findings = [item for item in findings if not self._has_citation(item)]
        unsupported_risks = [item for item in risks if not self._has_citation(item)]

        reduce_confidence = False
        suggested_confidence = float(answer.get("confidence_score", confidence_score) or 0.0)
        retry_reasons: List[str] = []

        if coverage < 0.55:
            reduce_confidence = True
            suggested_confidence = min(suggested_confidence, 0.45)
            retry_reasons.append("low_coverage")
        if not citations_present:
            reduce_confidence = True
            suggested_confidence = min(suggested_confidence, 0.35)
            retry_reasons.append("missing_citations")
        if unsupported_findings or unsupported_risks:
            reduce_confidence = True
            suggested_confidence = min(suggested_confidence, 0.4)
            retry_reasons.append("unsupported_claims")
        if confidence_score < 0.5:
            retry_reasons.append("low_confidence")

        summary_bits: List[str] = []
        if coverage < 0.55:
            summary_bits.append("Answer may not cover all parts of the question.")
        if not citations_present:
            summary_bits.append("No citations present for major claims.")
        if unsupported_findings or unsupported_risks:
            summary_bits.append("Some claims appear without citations.")
        if not summary_bits:
            summary_bits.append("Answer appears supported by retrieved evidence.")

        should_retry = bool(retry_reasons)

        report = CriticReport(
            answered_coverage=round(coverage, 3),
            missing_aspects=missing_aspects,
            citations_present=citations_present,
            unsupported_findings=unsupported_findings,
            unsupported_risks=unsupported_risks,
            evidence_strength=round(evidence_strength, 3),
            source_quality=round(source_quality, 3),
            contradiction_level=round(contradiction_level, 3),
            confidence_score=round(confidence_score, 3),
            reduce_confidence=reduce_confidence,
            suggested_confidence=round(suggested_confidence, 3),
            should_retry=should_retry,
            retry_reasons=retry_reasons,
            summary=" ".join(summary_bits),
        )

        return {
            "answered_coverage": report.answered_coverage,
            "missing_aspects": report.missing_aspects,
            "citations_present": report.citations_present,
            "unsupported_findings": report.unsupported_findings,
            "unsupported_risks": report.unsupported_risks,
            "evidence_strength": report.evidence_strength,
            "source_quality": report.source_quality,
            "contradiction_level": report.contradiction_level,
            "confidence_score": report.confidence_score,
            "reduce_confidence": report.reduce_confidence,
            "suggested_confidence": report.suggested_confidence,
            "should_retry": report.should_retry,
            "retry_reasons": report.retry_reasons,
            "summary": report.summary,
        }

    def _evidence_quality(self, rows: List[Dict[str, Any]]) -> Tuple[float, float]:
        if not rows:
            return 0.0, 0.0

        evidence_scores: List[float] = []
        trust_scores: List[float] = []
        for row in rows:
            score = row.get("evidence_score", row.get("final_score", row.get("score", 0.0)))
            try:
                evidence_scores.append(float(score))
            except (TypeError, ValueError):
                evidence_scores.append(0.0)

            breakdown = row.get("evidence_breakdown", {})
            trust = breakdown.get("trustworthiness")
            if trust is None:
                trust = self._trustworthiness(row)
            try:
                trust_scores.append(float(trust))
            except (TypeError, ValueError):
                trust_scores.append(0.0)

        evidence_strength = sum(evidence_scores) / max(len(evidence_scores), 1)
        source_quality = sum(trust_scores) / max(len(trust_scores), 1)
        return min(max(evidence_strength, 0.0), 1.0), min(max(source_quality, 0.0), 1.0)

    def _trustworthiness(self, row: Dict[str, Any]) -> float:
        trust_tier = str(row.get("trust_tier", "")).lower()
        source_type = str(row.get("source_type", "")).lower()

        if "internal" in trust_tier:
            return 0.9
        if "external" in trust_tier or source_type == "web":
            return 0.4
        if source_type in {"annual", "earnings", "presentations"}:
            return 0.85
        filename = str(row.get("filename", "")).lower()
        if "sec" in filename or "10-k" in filename or "10k" in filename:
            return 0.85
        return 0.6

    def _contradiction_level(self, findings: List[str], risks: List[str]) -> float:
        text = " ".join(findings + risks).lower()
        if not text:
            return 0.0

        positive_terms = {"increase", "growth", "up", "improve", "higher", "expand"}
        negative_terms = {"decrease", "decline", "down", "worse", "lower", "contract"}
        pos = any(term in text for term in positive_terms)
        neg = any(term in text for term in negative_terms)
        if pos and neg:
            return 0.6
        return 0.0

    def _confidence_score(
        self,
        evidence_strength: float,
        source_quality: float,
        completeness: float,
        contradiction_level: float,
    ) -> float:
        contradiction_component = 1.0 - min(max(contradiction_level, 0.0), 1.0)
        score = (
            evidence_strength * 0.4
            + source_quality * 0.25
            + completeness * 0.25
            + contradiction_component * 0.1
        )
        return round(min(max(score, 0.0), 1.0), 3)

    def _coverage_ratio(self, question: str, findings: List[str], risks: List[str]) -> float:
        question_terms = self._keywords(question)
        if not question_terms:
            return 0.0

        body_terms = set(self._keywords(" ".join(findings + risks)))
        overlap = [term for term in question_terms if term in body_terms]
        return len(overlap) / max(len(question_terms), 1)

    def _missing_aspects(self, question: str, findings: List[str], risks: List[str]) -> List[str]:
        question_terms = self._keywords(question)
        if not question_terms:
            return []

        body_terms = set(self._keywords(" ".join(findings + risks)))
        missing = [term for term in question_terms if term not in body_terms]
        return missing[:6]

    def _has_citation(self, text: str) -> bool:
        return "[" in text and "]" in text

    def _keywords(self, text: str) -> List[str]:
        tokens = [token.strip(".,;:()[]{}\"'\n\t").lower() for token in text.split()]
        return [token for token in tokens if token and token not in _STOPWORDS]
