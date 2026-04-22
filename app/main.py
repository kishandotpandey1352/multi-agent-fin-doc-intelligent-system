from fastapi import FastAPI

from app.config.settings import load_settings
from app.config.tracing import configure_langsmith
from app.utils.logging import setup_logging


def bootstrap() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    configure_langsmith(settings)


app = FastAPI(title="Multi-Agent Financial Document Intelligence System")


@app.on_event("startup")
def on_startup() -> None:
    bootstrap()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    bootstrap()
