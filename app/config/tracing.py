import logging
import os

from app.config.settings import Settings


logger = logging.getLogger(__name__)


def configure_langsmith(settings: Settings) -> bool:
    if not settings.langsmith_api_key:
        logger.info("LANGSMITH_API_KEY is not set. LangSmith tracing is disabled.")
        return False

    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2

    logger.info("LangSmith tracing enabled for project '%s'.", settings.langsmith_project)
    return True
