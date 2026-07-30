from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.document import RetrievedChunkResponse

class RetrievalMode(str, Enum):
    vector = "vector"
    keyword = "keyword"
    hybrid = "hybrid"

class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    category: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid

class QuestionResponse(BaseModel):
    question: str
    answer: str
    retrieval_mode: RetrievalMode
    used_chunks: list[RetrievedChunkResponse]