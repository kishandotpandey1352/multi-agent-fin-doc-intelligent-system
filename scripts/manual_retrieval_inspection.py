import json
from pathlib import Path

from app.retrieval.retriever import RetrievalRequest, Retriever


DATASET_PATH = Path("data/eval/baseline_questions_v1.jsonl")


def load_questions(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


if __name__ == "__main__":
    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset not found: {DATASET_PATH}")

    retriever = Retriever()

    print("Manual retrieval inspection (first 8 questions)\n")
    for idx, item in enumerate(load_questions(DATASET_PATH), start=1):
        if idx > 8:
            break

        request = RetrievalRequest(
            question=item["question"],
            company=item.get("company"),
            source_type=item.get("source_type"),
            top_k=12,
            final_k=5,
            source="local",
        )
        response = retriever.retrieve(request)

        print(f"{item['id']} | {item['question_type']}")
        print(f"Q: {item['question']}")
        print(f"Rewritten: {response['rewritten_query']}")

        if not response["results"]:
            print("  No retrieval hits\n")
            continue

        for rank, row in enumerate(response["results"][:3], start=1):
            preview = row["text"][:140].replace("\n", " ")
            print(
                f"  {rank}. score={row['final_score']:.4f} | {row['filename']} | "
                f"p{row['page_number']} | {row['source_type']}"
            )
            print(f"     {preview}...")
        print()
