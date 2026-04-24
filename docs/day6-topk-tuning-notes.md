# Day 6 Top-k Tuning Notes

## Scope
Tuning was run against `data/eval/baseline_questions_v1.jsonl` (15 questions) using local document retrieval.

## Settings Tested
- `top_k=8`, `final_k=5`
- `top_k=12`, `final_k=8`
- `top_k=20`, `final_k=10`

## Results
All three settings returned at least one hit for all 15 questions in the current indexed dataset.

- `top_k=8`: 15/15 questions with hits
- `top_k=12`: 15/15 questions with hits
- `top_k=20`: 15/15 questions with hits

Per-question-type hit coverage was 3/3 for:
- factual_extraction
- summary
- trend
- risk
- insufficient_evidence

## Selection Decision
Use `top_k=12` and `final_k=8` as default.

Reasoning:
- `top_k=8` is efficient but may be less robust as corpus diversity grows.
- `top_k=20` is more expensive without measurable benefit on this baseline set.
- `top_k=12` balances recall and latency for current corpus size.

## Follow-up
When corpus size increases significantly, rerun tuning and include:
- precision@k on labeled evidence
- latency measurements
- unsupported-answer rate for insufficient-evidence questions
