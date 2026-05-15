from app.graph.answer_flow import run_answer_pipeline


EXAMPLES = [
    {
        "query": "What were Tesla's key risk factors discussed in recent annual reporting?",
        "company": "tesla",
    },
    {
        "query": "Summarize Nvidia demand drivers from recent disclosures",
        "company": "nvidia",
    },
    {
        "query": "Compare Apple and Tesla commentary on margin pressure",
        "company": None,
    },
    {
        "query": "Create a chart of Tesla revenue trend over recent years",
        "company": "tesla",
    },
]


if __name__ == "__main__":
    for idx, item in enumerate(EXAMPLES, start=1):
        state = run_answer_pipeline(
            query=item["query"],
            company=item.get("company"),
        )

        print(f"\n=== Example {idx} ===")
        print(f"Query: {state['query']}")
        print(f"Intent: {state['plan']['intent']}")
        print(f"Retrieval Source: {state['retrieval'].get('source', 'unknown')}")
        print(f"Evidence Count: {state['answer']['evidence_count']}")
        print("\nExecutive summary")
        summary = state["answer"]["executive_summary"].encode("ascii", errors="replace").decode("ascii")
        print(summary)

        print("\nFindings")
        for item in state["answer"]["findings"]:
            line = item.encode("ascii", errors="replace").decode("ascii")
            print(f"- {line}")

        print("\nRisks")
        for item in state["answer"]["risks"]:
            line = item.encode("ascii", errors="replace").decode("ascii")
            print(f"- {line}")

        print("\nCitations")
        for item in state["answer"]["citations_formatted"]:
            line = item.encode("ascii", errors="replace").decode("ascii")
            print(f"- {line}")

        print("\nConfidence score")
        print(state["answer"]["confidence_score"])
        print(state["answer"]["confidence_note"])
