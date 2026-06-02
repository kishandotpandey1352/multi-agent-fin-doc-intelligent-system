from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    staged_path: str


class IndexResponse(BaseModel):
    documents: int
    chunks: int
    vectors: int


class AnswerResponse(BaseModel):
    answer: str
    executive_summary: str
    highlights: Optional[List[str]] = None
    numeric_values: Optional[List[str]] = None
    charts: Optional[List[Dict[str, Any]]] = None
    findings: List[str]
    risks: List[str]
    citations: List[Dict[str, Any]]
    citations_formatted: List[str]
    confidence_score: float
    confidence_note: str
    evidence_count: int
    plan: Optional[Dict[str, Any]] = None
    retrieval: Optional[Dict[str, Any]] = None
    critic: Optional[Dict[str, Any]] = None
