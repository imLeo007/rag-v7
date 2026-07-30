from datetime import datetime

from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    category: str
    created_at: datetime

class DocumentDetailResponse(DocumentResponse):
    total_chunks: int

class DocumentUploadResponse(BaseModel):
    message: str
    document_id: int
    filename: str
    category: str
    chunks_created: int

class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: int

class RetrievedChunkResponse(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    text: str
    page_number: int
    chunk_index: int

    vector_score: float | None = None
    keyword_score: float | None = None
    rerank_score: float | None = None