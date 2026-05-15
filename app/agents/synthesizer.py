from typing import Any, Dict, List, Tuple


class Synthesizer:
    def synthesize(self, query: str, intent: str, retrieved_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not retrieved_rows:
            return {
                "executive_summary": (
                    "I could not find enough evidence in retrieved chunks to answer this request. "
                    "Please try rephrasing the question or broadening filters."
                ),
                "findings": [],
                "risks": [],
                "citations": [],
                "citations_formatted": [],
                "confidence_score": 0.0,
                "confidence_note": "Low confidence: no supporting evidence retrieved.",
                "evidence_count": 0,
                "answer": "",
            }

        findings: List[str] = []
        risks: List[str] = []
        citations: List[Dict[str, Any]] = []
        citations_formatted: List[str] = []
        scores: List[float] = []

        def extract_text(row: Dict[str, Any], limit: int = 240) -> str:
            text = str(row.get("text", "")).strip().replace("\n", " ")
            text = " ".join(text.split())
            if len(text) > limit:
                return text[: limit - 3] + "..."
            return text

        def citation_label(idx: int, row: Dict[str, Any]) -> str:
            filename = str(row.get("filename", "unknown"))
            page = int(row.get("page_number", 0) or 0)
            return f"[{idx}] {filename} (page {page})"

        def classify_excerpt(text: str) -> str:
            lowered = text.lower()
            if "risk" in lowered or "uncertain" in lowered or "adverse" in lowered:
                return "risk"
            return "finding"

        # Keep this extractive to avoid unsupported claims.
        for idx, row in enumerate(retrieved_rows[:5], start=1):
            text = extract_text(row)
            label = citation_label(idx, row)
            entry = f"{label} {text}"
            if classify_excerpt(text) == "risk":
                risks.append(entry)
            else:
                findings.append(entry)

            score = float(row.get("final_score", row.get("score", 0.0)) or 0.0)
            scores.append(score)
            citations.append(
                {
                    "id": idx,
                    "filename": str(row.get("filename", "unknown")),
                    "page_number": int(row.get("page_number", 0) or 0),
                    "score": score,
                }
            )
            citations_formatted.append(label)

        executive_summary = findings[0] if findings else (risks[0] if risks else "")
        confidence_score, confidence_note = self._confidence(scores, len(citations))
        answer = self._format_output(
            executive_summary=executive_summary,
            findings=findings,
            risks=risks,
            citations_formatted=citations_formatted,
            confidence_score=confidence_score,
            confidence_note=confidence_note,
        )

        return {
            "executive_summary": executive_summary,
            "findings": findings,
            "risks": risks,
            "citations": citations,
            "citations_formatted": citations_formatted,
            "confidence_score": confidence_score,
            "confidence_note": confidence_note,
            "answer": answer,
            "evidence_count": len(citations),
        }

    def _confidence(self, scores: List[float], evidence_count: int) -> Tuple[float, str]:
        if not scores or evidence_count == 0:
            return 0.0, "Low confidence: no supporting evidence retrieved."

        avg_score = sum(scores) / max(len(scores), 1)
        score_component = min(max(avg_score, 0.0), 1.0)
        count_component = min(evidence_count / 5.0, 1.0)
        confidence = round((score_component * 0.7 + count_component * 0.3), 3)

        if confidence >= 0.75:
            note = "High confidence: multiple high-scoring citations support this answer."
        elif confidence >= 0.5:
            note = "Medium confidence: evidence is present but limited in score or coverage."
        else:
            note = "Low confidence: evidence is weak or sparse; verify against sources."

        return confidence, note

    def _format_output(
        self,
        executive_summary: str,
        findings: List[str],
        risks: List[str],
        citations_formatted: List[str],
        confidence_score: float,
        confidence_note: str,
    ) -> str:
        summary_block = executive_summary or "No executive summary generated."
        findings_block = findings or ["No findings extracted from retrieved evidence."]
        risks_block = risks or ["No explicit risk statements detected in retrieved evidence."]
        citations_block = citations_formatted or ["No citations available."]

        output_lines = [
            "Executive summary",
            summary_block,
            "",
            "Findings",
            *findings_block,
            "",
            "Risks",
            *risks_block,
            "",
            "Citations",
            *citations_block,
            "",
            f"Confidence score: {confidence_score}",
            confidence_note,
        ]
        return "\n".join(output_lines)
