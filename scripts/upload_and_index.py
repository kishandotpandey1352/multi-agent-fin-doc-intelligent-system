import argparse
from pathlib import Path

from app.ingestion.upload import stage_uploaded_pdf
from app.retrieval.pipeline import build_index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload one PDF and index it")
    parser.add_argument("--file", required=True, help="Path to PDF file")
    parser.add_argument("--company", required=True, help="tesla|apple|nvidia|research")
    parser.add_argument("--source-type", required=True, help="annual|earnings|presentations|research")
    parser.add_argument("--append", action="store_true", help="Append to existing index")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page cap for quick runs")
    args = parser.parse_args()

    staged = stage_uploaded_pdf(
        file_path=Path(args.file),
        company=args.company,
        source_type=args.source_type,
    )
    print(f"Staged: {staged}")

    stats = build_index(
        company_filters=[args.company],
        max_pages=args.max_pages,
        reset_index=not args.append,
    )
    print("\nIndex update complete")
    print(f"Documents indexed: {stats['documents']}")
    print(f"Chunks indexed: {stats['chunks']}")
