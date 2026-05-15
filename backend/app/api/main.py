from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.utils.paths import ensure_repo_root_on_path

ensure_repo_root_on_path()

from backend.app.routes import charts, comparison, indexing, qa, summary, upload


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
