# Multi-Agent Financial Document Intelligence System

An AI-powered, multi-agent system for analyzing financial documents, answering complex questions with citations, generating insights and charts, and retrieving external information when local evidence is insufficient.

## Why This Project

Financial documents such as annual reports, 10-Ks, and earnings statements are dense and time-consuming to analyze. This system is designed to make financial research faster and more reliable by combining retrieval, reasoning, validation, and critique in a single workflow.

## What It Does

- Ingests and understands financial documents (PDF-focused).
- Answers questions using evidence-backed citations.
- Produces structured outputs (summary, insights, risks, recommendations).
- Generates trend charts (for example, revenue over time).
- Falls back to web retrieval when document evidence is missing.
- Applies evaluation and critique loops to reduce hallucinations.

## Core Features

- **Document Intelligence**: Upload and analyze financial filings and reports.
- **Citation-Grounded Q&A**: Responses are tied to source evidence.
- **Hybrid Retrieval**: Combines local vector retrieval with web fallback.
- **Multi-Agent Workflow**: Planner, Retriever, Evaluator, Synthesizer, and Critic.
- **Reliability Controls**: Evidence scoring, unsupported-claim checks, retry logic.
- **Observability**: Tracing, latency/cost tracking, and evaluation diagnostics.

## Architecture (Concept)

The system is designed around LangGraph orchestration:

1. User uploads a document and asks a question.
2. Planner decomposes the problem into retrievable sub-questions.
3. Retriever collects candidate evidence from local docs and (optionally) the web.
4. Evaluator scores evidence quality and relevance.
5. Synthesizer builds a structured answer with citations.
6. Critic validates groundedness and triggers retries when needed.
7. Final response is returned with confidence metadata.

## Suggested Tech Stack

- **Orchestration**: LangGraph, LangChain
- **Vector Retrieval**: FAISS
- **Backend API**: FastAPI
- **Frontend**: Streamlit
- **Models**: Open-source LLMs (for example, LLaMA, Mistral)
- **Embeddings**: Open-source embedding models
- **Data Processing**: Python, Pandas
- **Observability / Evaluation**: LangSmith

## Example Use Cases

- Analyze annual reports (10-K/10-Q/earnings reports).
- Extract financial risks and key metrics.
- Compare company performance across periods.
- Build revenue trend charts from extracted data.
- Answer investment-research questions with source citations.

## Example Query

> Analyze Tesla's financial performance and show the revenue trend over the last 5 years.

Expected output:

- Executive summary
- Key financial insights
- Risks and opportunities
- Revenue trend visualization
- Source citations
- Confidence score

## Evaluation Strategy

Track quality and reliability using:

- Answer correctness
- Groundedness (faithfulness to sources)
- Citation accuracy
- Retrieval relevance
- Latency and cost
- Retry frequency

Recommended approach: evaluate against a curated financial Q&A set and inspect traces for retrieval and reasoning failures.

## Failure Handling and Retry Logic

The system should trigger retries when it detects:

- Insufficient evidence
- Incomplete answers
- Unsupported claims

Retry actions can include:

- Re-retrieving evidence
- Re-planning query decomposition
- Re-synthesizing the final response
- Returning a controlled fallback when confidence is low

## Day 2 Deliverables (System Design)

- [Architecture draft](docs/architecture-draft.md)
- [Workflow diagram draft](docs/workflow-diagram-draft.md)
- [State schema document](docs/state-schema.md)

These documents lock the design for:

- Graph workflow
- State schema
- Agent responsibilities
- Routing and retry logic

## Day 3 Deliverables (Data and Retrieval Design)

- [Retrieval design doc](docs/day3-retrieval-design.md)
- [Metadata schema finalized](docs/day3-metadata-schema.md)
- [Model/store choices finalized](docs/day3-model-store-decisions.md)

Day 3 focus locks decisions for:

- Document source coverage
- Chunking and metadata strategy
- Embedding, vector store, and app DB choices

## Day 4 Deliverables (Repo and Scaffolding Setup)

- Base app structure created under `app/` (agents, graph, ingestion, retrieval, evaluation, charts, api, utils, config)
- Environment template added: `.env.example`
- Dependency management updated: `requirements.txt`, `requirements-dev.txt`
- Base logging scaffold added: `app/utils/logging.py`
- LangSmith tracing setup added: `app/config/tracing.py`

Day 4 quick setup:

```bash
copy .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

LangSmith enablement:

1. Set `LANGSMITH_API_KEY` in `.env`.
2. Optionally set `LANGSMITH_PROJECT`.
3. Keep `LANGCHAIN_TRACING_V2=true`.

## Day 5 Deliverables (Baseline Eval + Ingestion Pipeline)

- Baseline eval dataset added: `data/eval/baseline_questions_v1.jsonl` (15 questions)
- Ingestion flow supports upload-and-index path: `scripts/upload_and_index.py`
- Baseline eval runner added: `scripts/run_baseline_eval.py`

Day 5 data flow command examples:

```bash
# 1) Full indexing from data/ folders
python -m scripts.build_index

# 2) Upload one PDF and index only that company scope
python -m scripts.upload_and_index --file "C:\path\to\report.pdf" --company tesla --source-type annual --append

# 3) Run baseline retrieval evaluation
python -m scripts.run_baseline_eval
```

Pipeline coverage in code:

- PDF loading and text extraction: `app/ingestion/pdf_loader.py`
- Text cleaning: `app/ingestion/pdf_loader.py`
- Metadata inference/validation: `app/retrieval/metadata.py`
- Chunking: `app/retrieval/chunking.py`
- Embeddings: `app/retrieval/embedding.py`
- FAISS indexing (with NumPy fallback): `app/retrieval/vector_store.py`
- Build orchestration: `app/retrieval/pipeline.py`

## Day 6 Deliverables (Retriever Implementation)

- Retriever abstraction added: `app/retrieval/retriever.py`
- Question rewriting added in retriever preprocessing
- Local-vs-web retrieval path separated with web search fallback implementation
- Retrieval quality test script added: `scripts/evaluate_retrieval_quality.py`
- Manual retrieval inspection script added: `scripts/manual_retrieval_inspection.py`
- Top-k tuning notes saved: `docs/day6-topk-tuning-notes.md`
- Manual inspection notes saved: `docs/day6-manual-retrieval-inspection.md`

Day 6 command examples:

```bash
# Retrieval quality checks
python -m scripts.evaluate_retrieval_quality --top-k 12 --final-k 8

# Manual inspection of retrieved chunks
python -m scripts.manual_retrieval_inspection
```

## Day 3 Quick Start (Local Retrieval)

After placing PDFs in `data/`, run:

```bash
pip install -r requirements.txt
python -m scripts.build_index --max-docs 6 --max-pages 8 --companies tesla apple nvidia
python -m scripts.smoke_test
```

Full build:

```bash
python -m scripts.build_index
```

Generated artifacts:

- `data/index/faiss.index` (when FAISS is available)
- `data/index/faiss.npy` (NumPy fallback when FAISS is unavailable)
- `data/index/metadata.db`

## Getting Started

> Note: This repository is currently at an early stage. The commands below represent the intended setup once implementation files are in place.

1. Clone the repository.

```bash
git clone https://github.com/your-username/multi-agent-fin-doc-intelligent-system.git
cd multi-agent-fin-doc-intelligent-system
```

2. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Configure environment variables.

```bash
copy .env.example .env
```

5. Run backend and frontend (once implemented).

```bash
uvicorn app.main:app --reload
streamlit run app/ui.py
```

## Proposed Project Structure

```text
app/
	agents/
	graph/
	ingestion/
	retrieval/
	evaluation/
	charts/
	api/
	utils/
	config/
docs/
	architecture.png
	workflow.png
data/
tests/
```
## Data collection links
- https://ir.tesla.com/#quarterly-disclosure
- https://ir.tesla.com/sec-filings

### NVIDIA

## Roadmap

- Advanced table extraction from financial PDFs
- Real-time market/financial data integration
- Multi-document and multi-company comparison
- Automatic KPI detection (for example, EBITDA, margins)
- Domain-adapted model fine-tuning
- User/session memory for iterative analysis workflows

## Contributing

Contributions are welcome. Open an issue for bugs or feature ideas, or submit a pull request with clear scope and test notes.

## License

MIT License

## Summary

This project demonstrates a practical financial AI assistant pattern: multi-agent orchestration, citation-grounded retrieval-augmented generation, and LLMOps-style observability for trustworthy outputs.