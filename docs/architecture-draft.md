# Day 2 Architecture Draft

## Objective
Define and lock the multi-agent orchestration design before coding.

## Locked Workflow
User Query -> Planner -> Retriever -> Evidence Evaluator -> Synthesizer -> Critic -> Final or Retry or Re-plan

## Agent Responsibilities

### Planner
- Classify `question_type` (for example: summary, metric extraction, trend, comparison, risk analysis).
- Break down complex questions into a plan of sub-questions.
- Define retrieval intent per step (local docs only or local + web fallback).
- Trigger re-planning when Critic indicates query misunderstanding.

### Retriever
- Retrieve relevant evidence from indexed local documents.
- Trigger web fallback retrieval if local evidence is insufficient.
- Return scored candidate chunks with metadata (source, page, relevance).

### Evidence Evaluator
- Score evidence quality (relevance, specificity, trustworthiness, recency).
- Remove weak/duplicate evidence.
- Produce `approved_evidence` set used by Synthesizer.

### Synthesizer
- Generate a structured answer from `approved_evidence`.
- Attach explicit citations to each major claim.
- Estimate confidence based on evidence quality and coverage.

### Critic
- Verify answer coverage against original query and plan.
- Verify grounding (each claim should map to approved evidence).
- Detect failure mode and route to retry path:
  - low evidence
  - misunderstood question
  - incomplete answer

## Routing and Retry Logic

### Routing Rules
- If low evidence -> route to Retriever (retrieve again).
- If question misunderstood -> route to Planner (re-plan).
- If answer incomplete -> route to Synthesizer (synthesize again).
- If retry limit exceeded -> return low-confidence answer with explicit caveat.

### Retry Policy
- `MAX_RETRIES = 3`
- Increment `retry_count` on each retry loop.
- Priority order for retry route selection:
  1. misunderstanding -> Planner
  2. low evidence -> Retriever
  3. incomplete answer -> Synthesizer
- When `retry_count >= MAX_RETRIES`, force finalize with:
  - best effort answer
  - confidence downgraded
  - clear statement of limitations

## Node-Level Inputs and Outputs

### Planner
- Inputs: `user_query`, `retry_count`, optional `critic_report`
- Outputs: `question_type`, `plan`

### Retriever
- Inputs: `user_query`, `question_type`, `plan`
- Outputs: `retrieved_docs`

### Evidence Evaluator
- Inputs: `retrieved_docs`, `question_type`
- Outputs: `approved_evidence`

### Synthesizer
- Inputs: `user_query`, `question_type`, `plan`, `approved_evidence`
- Outputs: `draft_answer`, `citations`, `confidence_score`

### Critic
- Inputs: `user_query`, `plan`, `approved_evidence`, `draft_answer`, `citations`, `confidence_score`
- Outputs: `critic_report`, route decision (`final`, `retry_retrieve`, `replan`, `retry_synthesize`)

## Implementation Notes for Day 3
- Implement each agent as a separate LangGraph node.
- Keep state immutable per step (append/replace only specific fields).
- Add structured logs for each route decision and retry reason.
