from app.retrieval.search import search


TEST_QUERIES = [
    ("tesla", "Summarize Tesla revenue trend over recent years"),
    ("apple", "What are key risks discussed in recent Apple reports?"),
    ("nvidia", "How has Nvidia described demand drivers in recent periods?"),
]


if __name__ == "__main__":
    for company, query in TEST_QUERIES:
        print(f"\n=== {company.upper()} ===")
        print(f"Query: {query}")

        results = search(query=query, company=company)

        if not results:
            print("No evidence returned.")
            continue

        for i, row in enumerate(results[:3], start=1):
            preview = row["text"][:220].replace("\n", " ")
            print(
                f"{i}. score={row['final_score']:.4f} | {row['filename']} | "
                f"page={row['page_number']} | trust={row['trust_tier']}"
            )
            print(f"   {preview}...")
