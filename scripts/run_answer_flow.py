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
        print("Answer:")

        answer_text = state["answer"]["answer"].encode("ascii", errors="replace").decode("ascii")
        print(answer_text)

        print("Citations:")
        for citation in state["answer"]["citations"]:
            print(
                f"  - [{citation['id']}] {citation['filename']} "
                f"(page={citation['page_number']}, score={citation['score']})"
            )
