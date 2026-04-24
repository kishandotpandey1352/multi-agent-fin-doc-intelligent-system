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

    total = 0
    with_hits = 0
    retriever = Retriever()

    for item in load_questions(DATASET_PATH):
        total += 1
        request = RetrievalRequest(
            question=item["question"],
            company=item["company"],
            source_type=item["source_type"],
            source="local",
        )
        response = retriever.retrieve(request)
        results = response["results"]
        hit = len(results) > 0
        if hit:
            with_hits += 1

        top = results[0] if results else None
        print(f"{item['id']} | {item['question_type']} | hits={len(results)}")
        if top:
            print(f"  top: {top['filename']} p{top['page_number']} score={top['final_score']:.4f}")

    print("\nBaseline eval retrieval summary")
    print(f"Questions: {total}")
    print(f"Questions with >=1 hit: {with_hits}")
