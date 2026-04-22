import argparse

from app.retrieval.pipeline import build_index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Day 3 retrieval index")
    parser.add_argument("--max-docs", type=int, default=None, help="Index only first N PDFs")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Limit pages per PDF for faster dry runs",
    )
    parser.add_argument(
        "--companies",
        nargs="*",
        default=None,
        help="Optional company filter, e.g. tesla apple nvidia research",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing index/database instead of resetting",
    )
    args = parser.parse_args()

    stats = build_index(
        max_docs=args.max_docs,
        company_filters=args.companies,
        max_pages=args.max_pages,
        reset_index=not args.append,
    )
    print("\nBuild complete")
    print(f"Documents indexed: {stats['documents']}")
    print(f"Chunks indexed: {stats['chunks']}")
