from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


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
    reduce_confidence: bool
    suggested_confidence: float
    summary: str


class Critic:
    def review(self, question: str, answer: Dict[str, Any]) -> Dict[str, Any]:
        findings = list(answer.get("findings", []))
        risks = list(answer.get("risks", []))
        citations = list(answer.get("citations", []))

        coverage = self._coverage_ratio(question, findings, risks)
        missing_aspects = self._missing_aspects(question, findings, risks)

        citations_present = bool(citations)
        unsupported_findings = [item for item in findings if not self._has_citation(item)]
        unsupported_risks = [item for item in risks if not self._has_citation(item)]

        reduce_confidence = False
        suggested_confidence = float(answer.get("confidence_score", 0.0) or 0.0)

        if coverage < 0.55:
            reduce_confidence = True
            suggested_confidence = min(suggested_confidence, 0.45)
        if not citations_present:
            reduce_confidence = True
            suggested_confidence = min(suggested_confidence, 0.35)
        if unsupported_findings or unsupported_risks:
            reduce_confidence = True
            suggested_confidence = min(suggested_confidence, 0.4)

        summary_bits: List[str] = []
        if coverage < 0.55:
            summary_bits.append("Answer may not cover all parts of the question.")
        if not citations_present:
            summary_bits.append("No citations present for major claims.")
        if unsupported_findings or unsupported_risks:
            summary_bits.append("Some claims appear without citations.")
        if not summary_bits:
            summary_bits.append("Answer appears supported by retrieved evidence.")

        report = CriticReport(
            answered_coverage=round(coverage, 3),
            missing_aspects=missing_aspects,
            citations_present=citations_present,
            unsupported_findings=unsupported_findings,
            unsupported_risks=unsupported_risks,
            reduce_confidence=reduce_confidence,
            suggested_confidence=round(suggested_confidence, 3),
            summary=" ".join(summary_bits),
        )

        return {
            "answered_coverage": report.answered_coverage,
            "missing_aspects": report.missing_aspects,
            "citations_present": report.citations_present,
            "unsupported_findings": report.unsupported_findings,
            "unsupported_risks": report.unsupported_risks,
            "reduce_confidence": report.reduce_confidence,
            "suggested_confidence": report.suggested_confidence,
            "summary": report.summary,
        }

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
