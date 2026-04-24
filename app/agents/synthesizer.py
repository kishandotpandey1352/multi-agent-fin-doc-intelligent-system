from typing import Any, Dict, List


class Synthesizer:
    def synthesize(self, query: str, intent: str, retrieved_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not retrieved_rows:
            return {
                "answer": (
                    "I could not find enough evidence in retrieved chunks to answer this request. "
                    "Please try rephrasing the question or broadening filters."
                ),
                "citations": [],
                "evidence_count": 0,
            }

        lines: List[str] = []
        citations: List[Dict[str, Any]] = []

        # Keep this extractive to avoid unsupported claims.
        for idx, row in enumerate(retrieved_rows[:5], start=1):
            text = str(row.get("text", "")).strip().replace("\n", " ")
            text = " ".join(text.split())
            if len(text) > 240:
                text = text[:237] + "..."

            filename = str(row.get("filename", "unknown"))
            page = int(row.get("page_number", 0) or 0)
            citation_tag = f"[{idx}]"
            lines.append(f"{citation_tag} {text}")

            citations.append(
                {
                    "id": idx,
                    "filename": filename,
                    "page_number": page,
                    "score": row.get("final_score", row.get("score", 0.0)),
                }
            )

        prefix_by_intent = {
            "qa": "Grounded answer (from retrieved evidence):",
            "summary": "Grounded summary (from retrieved evidence):",
            "chart_request": "Grounded chart-ready evidence points:",
            "comparative_analysis": "Grounded comparative evidence points:",
        }
        prefix = prefix_by_intent.get(intent, "Grounded answer (from retrieved evidence):")
        answer = prefix + "\n" + "\n".join(lines)

        return {
            "answer": answer,
            "citations": citations,
            "evidence_count": len(citations),
        }
