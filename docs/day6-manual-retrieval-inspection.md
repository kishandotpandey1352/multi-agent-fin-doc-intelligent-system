# Day 6 Manual Retrieval Inspection

## Method
Manual inspection was performed with:

```bash
python -m scripts.manual_retrieval_inspection
```

The script reviews the first 8 baseline questions and prints:
- rewritten query
- top 3 retrieved chunks
- scores, source file, and page number

## Observations
- Retrieval returns relevant company-scoped evidence for factual and risk prompts.
- Query rewriting is active (normalization and abbreviation expansion) and traceable in output.
- Returned evidence includes citation fields (`filename`, `page_number`, `source_type`).
- Some top results for summary/trend prompts include table-of-contents or generic forward-looking sections, indicating room for future reranking improvements.

## Conclusion
Manual inspection confirms retrieval is operational and inspectable for finance questions.

Next improvements (post-Day 6):
- section-aware reranking boost for financial statement sections
- richer query rewriting using LLM-based reformulation
- explicit insufficient-evidence confidence thresholding
