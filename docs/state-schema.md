# Day 2 State Schema

## State Object

```yaml
state:
  user_query: string
  question_type: string
  plan: list[string]
  retrieved_docs:
    - id: string
      source: string
      page: integer
      snippet: string
      retrieval_score: float
      source_type: string  # local or web
  approved_evidence:
    - id: string
      source: string
      page: integer
      snippet: string
      quality_score: float
      rationale: string
  draft_answer: string
  citations:
    - claim_id: string
      evidence_id: string
      source: string
      page: integer
  confidence_score: float
  critic_report:
    status: string          # pass or fail
    failure_mode: string    # low_evidence, misunderstood_question, incomplete_answer, none
    coverage_notes: string
    grounding_notes: string
    suggested_route: string # final, retry_retrieve, replan, retry_synthesize
  retry_count: integer
  final_answer: string
```

## Field Definitions

| Field | Type | Set By | Purpose |
| --- | --- | --- | --- |
| `user_query` | string | User/Input layer | Original request from user |
| `question_type` | string | Planner | Task category used for planning and retrieval strategy |
| `plan` | list[string] | Planner | Ordered sub-questions/steps |
| `retrieved_docs` | list[object] | Retriever | Candidate evidence from local/web sources |
| `approved_evidence` | list[object] | Evidence Evaluator | Filtered high-quality evidence for synthesis |
| `draft_answer` | string | Synthesizer | Candidate response before final approval |
| `citations` | list[object] | Synthesizer | Claim-to-evidence mapping |
| `confidence_score` | float | Synthesizer | Numeric confidence estimate (0.0 to 1.0) |
| `critic_report` | object | Critic | Validation output and routing signal |
| `retry_count` | integer | Orchestration layer | Number of retries used so far |
| `final_answer` | string | Finalization step | Output returned to user |

## Validation Rules
- `retry_count` starts at 0 and increments for every retry route.
- `confidence_score` must be in range [0.0, 1.0].
- Every major claim in `draft_answer` should map to an entry in `citations`.
- `critic_report.failure_mode` must be one of:
  - `low_evidence`
  - `misunderstood_question`
  - `incomplete_answer`
  - `none`
- If `retry_count >= MAX_RETRIES`, skip further retries and set `final_answer`.

## Recommended Constants

```text
MAX_RETRIES = 3
MIN_EVIDENCE_ITEMS = 3
MIN_CONFIDENCE_TO_FINALIZE = 0.60
```

## State Lifecycle
1. Initialize state with `user_query` and defaults.
2. Planner sets `question_type` and `plan`.
3. Retriever fills `retrieved_docs`.
4. Evaluator fills `approved_evidence`.
5. Synthesizer fills `draft_answer`, `citations`, `confidence_score`.
6. Critic fills `critic_report` and routing signal.
7. Orchestrator either retries (increment `retry_count`) or sets `final_answer`.
