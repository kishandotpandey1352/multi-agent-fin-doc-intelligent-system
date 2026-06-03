from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.utils.paths import ensure_repo_root_on_path

ensure_repo_root_on_path()

from backend.app.routes import charts, comparison, indexing, qa, summary, upload
from app.llm.ollama_client import get_ollama_client


app = FastAPI(title="Financial Doc Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(indexing.router)
app.include_router(qa.router)
app.include_router(summary.router)
app.include_router(charts.router)
app.include_router(comparison.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.on_event("startup")
def prewarm_ollama_model() -> None:
    """Trigger a lightweight call to Ollama to warm the model into memory on service start.

    This is best-effort — failures are ignored so the API still starts even if Ollama is unavailable.
    """
    try:
        client = get_ollama_client()
        if client:
            # non-blocking quick warm-up in a background thread
            import threading

            def _warm() -> None:
                try:
                    client.generate("Warmup.", max_tokens=8, temperature=0.0)
                except Exception:
                    pass

            threading.Thread(target=_warm, daemon=True).start()
    except Exception:
        pass
