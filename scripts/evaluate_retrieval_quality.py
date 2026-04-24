import argparse
import json
from collections import defaultdict
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
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality on baseline questions")
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--final-k", type=int, default=8)
    args = parser.parse_args()

    if not DATASET_PATH.exists():
        raise SystemExit(f"Dataset not found: {DATASET_PATH}")

    retriever = Retriever()
    by_type_total = defaultdict(int)
    by_type_hits = defaultdict(int)

    total = 0
    with_hits = 0

    for item in load_questions(DATASET_PATH):
        total += 1
        qtype = item["question_type"]
        by_type_total[qtype] += 1

        request = RetrievalRequest(
            question=item["question"],
            company=item.get("company"),
            source_type=item.get("source_type"),
            top_k=args.top_k,
            final_k=args.final_k,
            source="local",
        )
        response = retriever.retrieve(request)
        hits = len(response["results"])

        if hits > 0:
            with_hits += 1
            by_type_hits[qtype] += 1

        print(f"{item['id']} | {qtype} | hits={hits}")

    print("\nRetrieval quality summary")
    print(f"top_k={args.top_k}, final_k={args.final_k}")
    print(f"Questions: {total}")
    print(f"Questions with >=1 hit: {with_hits}")
    for qtype in sorted(by_type_total.keys()):
        hits = by_type_hits[qtype]
        size = by_type_total[qtype]
        ratio = (hits / size) * 100 if size else 0
        print(f"- {qtype}: {hits}/{size} ({ratio:.1f}%)")
