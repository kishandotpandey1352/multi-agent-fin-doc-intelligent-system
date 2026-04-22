from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass
class Settings:
    app_env: str
    log_level: str
    langsmith_api_key: str
    langsmith_project: str
    langsmith_endpoint: str
    langchain_tracing_v2: str


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY", ""),
        langsmith_project=os.getenv("LANGSMITH_PROJECT", "multi-agent-fin-doc-intel"),
        langsmith_endpoint=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        langchain_tracing_v2=os.getenv("LANGCHAIN_TRACING_V2", "true"),
    )
