from typing import List, Optional
from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    company: str = Field(..., description="tesla|apple|nvidia|research")
    source_type: str = Field(..., description="annual|earnings|presentations|research")


class IndexRequest(BaseModel):
    company_filters: Optional[List[str]] = None
    max_docs: Optional[int] = None
    max_pages: Optional[int] = None
    reset_index: bool = True


class AnswerRequest(BaseModel):
    question: str
    company: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None  # auto | local | web
    intent: Optional[str] = None  # qa | summary | chart_request | comparative_analysis
    top_k: Optional[int] = None
    final_k: Optional[int] = None
