from typing import Any

from app.ai.reranker import rerank_chunks

from time import perf_counter

from app.core.config import settings

from fastapi import HTTPException

import re

from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding import create_question_embeddings

from app.models.documentchunk import DocumentChunk

from app.models.document import Document

from app.schemas.question import RetrievalMode

RetrievedChunks = dict[str, Any]

async def retrieve_vector_chunks(
        question: str,
        db: AsyncSession,
        candidate_k: int,
        document_id: int | None = None,
        category: str | None = None,
) -> list[RetrievedChunks]:
    question_embedding = create_question_embeddings(question)

    vector_score = (
        1 - DocumentChunk.embeddings.cosine_distance(question_embedding)
    ).label("vector_score")

    query = (
        select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.page_number,
            DocumentChunk.text,
            Document.filename,
            vector_score
        ).join(Document, Document.id == DocumentChunk.document_id)
    )

    if category is not None:
        query = query.where(Document.category == category)

    if document_id is not None:
        query = query.where(DocumentChunk.document_id == document_id)

    query = (
        query.order_by(
            DocumentChunk.embeddings.cosine_distance(question_embedding)
        ).limit(candidate_k)
    )

    result = await db.execute(query)

    return [
        {
            "chunk_id": row.chunk_id,
            "document_id": row.document_id,
            "filename": row.filename,
            "text": row.text,
            "page_number": row.page_number,
            "chunk_index": row.chunk_index,
            "vector_score": float(row.vector_score),
            "keyword_score": None,
            "fusion_score": None,
            "rerank_score": None
        }
        for row in result.all()
    ]

async def retrieve_keyword_chunks(
        question: str,
        db: AsyncSession,
        candidate_k: int,
        document_id: int | None = None,
        category: str | None = None,
) -> list[RetrievedChunks]:

    cleaned = [
        term
        for term in re.findall(r"[A-Za-z0-9]+", question.lower())
        if len(term) > 2
    ]

    if not cleaned:
        return []

    tsquery_text = " OR ".join(cleaned)

    search_query = func.websearch_to_tsquery("english", tsquery_text)

    keyword_score = func.ts_rank_cd(
        DocumentChunk.search_vector,
        search_query,
    ).label("keyword_score")

    query = (
        select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id,
            DocumentChunk.text,
            DocumentChunk.page_number,
            DocumentChunk.chunk_index,
            Document.filename,
            keyword_score
        ).join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.search_vector.op("@@")(search_query))
    )

    if category is not None:
        query = query.where(Document.category == category)

    if document_id is not None:
        query = query.where(DocumentChunk.document_id == document_id)

    query = query.order_by(keyword_score.desc()).limit(candidate_k)

    result = await db.execute(query)

    return [
        {
            "chunk_id": row.chunk_id,
            "document_id": row.document_id,
            "filename": row.filename,
            "text": row.text,
            "page_number": row.page_number,
            "chunk_index": row.chunk_index,
            "vector_score": None,
            "keyword_score": float(row.keyword_score),
            "fusion_score": None,
            "rerank_score": None
        }
        for row in result.all()
    ]


def fuse_rankings(
        vector_results: list[RetrievedChunks],
        keyword_results: list[RetrievedChunks],
        top_k: int,
        rrf_constant: int = 60
) -> list[RetrievedChunks]:
    fused_results: dict[int, RetrievedChunks] = {}

    for rank, item in enumerate(vector_results, start=1):
        chunk_id = int(item["chunk_id"])

        fused_results[chunk_id] = item.copy()

        fused_results[chunk_id]["fusion_score"] = 1/(rrf_constant + rank)

    for rank, item in enumerate(keyword_results, start=1):
        chunk_id = item["chunk_id"]

        rrf_score = 1/(rrf_constant + rank)

        if chunk_id in fused_results:
            fused_results[chunk_id]["keyword_score"] = item["keyword_score"]
            fused_results[chunk_id]["fusion_score"] += rrf_score

        else:
            fused_results[chunk_id] = item.copy()
            fused_results[chunk_id]["fusion_score"] = rrf_score


    ranked_results = sorted(
        fused_results.values(),
        key=lambda item: float(item["fusion_score"] or 0),
        reverse=True
    )

    return ranked_results[:top_k]

async def retrieve_top_chunks(
    question: str,
    db: AsyncSession,
    top_k: int,
    retrieval_mode: RetrievalMode = RetrievalMode.hybrid,
    document_id: int | None = None,
    category: str | None = None,
) -> list[RetrievedChunks]:
    candidate_k = max(top_k * 3, 10)

    start = perf_counter()

    if retrieval_mode == RetrievalMode.vector:
        result = await retrieve_vector_chunks(question=question, db=db, candidate_k=candidate_k, document_id=document_id, category=category)
        print("vector retrieval: ", perf_counter() - start)

    elif retrieval_mode == RetrievalMode.keyword:
        result = await retrieve_keyword_chunks(question=question, db=db, candidate_k=candidate_k, document_id=document_id, category=category)
        print("keyword retrieval: ", perf_counter() - start)

    else:
        start = perf_counter()

        vector_results = await retrieve_vector_chunks(question=question, db=db, candidate_k=candidate_k, document_id=document_id, category=category)
        print("vector retrieval: ", perf_counter() - start)

        start = perf_counter()

        keyword_results = await retrieve_keyword_chunks(question=question, db=db, candidate_k=candidate_k, document_id=document_id, category=category)
        print("keyword retrieval: ", perf_counter() - start)

        start = perf_counter()

        fused_results = fuse_rankings(
            vector_results=vector_results,
            keyword_results=keyword_results,
            top_k=candidate_k
        )

        print("rrf fusion: ", perf_counter() - start)

        start = perf_counter()

        result = rerank_chunks(
            question=question,
            chunks=fused_results,
            top_k=top_k
        )

        print("reranker: ", perf_counter() - start)

    if not result:
        raise HTTPException(status_code=404, detail="Relevant information could not found in documents.")

    return result