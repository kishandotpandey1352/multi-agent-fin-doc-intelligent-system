# Day 2 Workflow Diagram Draft

```mermaid
flowchart TD
    U[User Query] --> P[Planner]
    P --> R[Retriever]
    R --> E[Evidence Evaluator]
    E --> S[Synthesizer]
    S --> C[Critic]

    C -->|Pass: grounded and complete| F[Final Answer]
    C -->|Low evidence| RR[Retry Retriever]
    C -->|Question misunderstood| RP[Re-plan via Planner]
    C -->|Answer incomplete| RS[Retry Synthesizer]

    RR --> RC{retry_count < MAX_RETRIES?}
    RP --> PC{retry_count < MAX_RETRIES?}
    RS --> SC{retry_count < MAX_RETRIES?}

    RC -->|Yes| R
    PC -->|Yes| P
    SC -->|Yes| S

    RC -->|No| L[Low-Confidence Final Answer]
    PC -->|No| L
    SC -->|No| L
```

## Locked Path
User Query -> Planner -> Retriever -> Evidence Evaluator -> Synthesizer -> Critic -> Final or Retry or Re-plan

## Retry Conditions
- Low evidence: go back to Retriever.
- Question misunderstood: go back to Planner.
- Answer incomplete: go back to Synthesizer.
- Retry limit exceeded: return low-confidence final answer.
