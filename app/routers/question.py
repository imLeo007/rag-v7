from typing import Annotated, Any

from fastapi import APIRouter, Depends

from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import generate_answer

from app.ai.prompt import build_rag_prompt

from app.core.database import get_db

from app.ai.retriever import retrieve_top_chunks

from app.schemas.document import RetrievedChunkResponse

from app.schemas.question import QuestionRequest, QuestionResponse

from app.services.document_service import get_document_by_id


router = APIRouter(prefix="/question", tags=["Question"])


SessionDB = Annotated[AsyncSession, Depends(get_db)]


def build_context(retrieved_chunks: list[dict[str, Any]]) -> str:
    context_parts: list[str] = []

    for pos, chunk in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"""
source {pos}
Filename: {chunk["filename"]}
Page: {chunk["page_number"]}
Chunk: {chunk["chunk_index"]}

context:
{chunk["text"]}
""".strip()
        )

    return "\n\n--\n\n".join(context_parts)


async def answer_question(request: QuestionRequest, db: AsyncSession, document_id: int | None = None) -> QuestionResponse:
    retrieved_chunks = await retrieve_top_chunks(
        question=request.question,
        category=request.category,
        db=db,
        top_k=request.top_k,
        retrieval_mode=request.retrieval_mode,
        document_id=document_id
    )

    context = build_context(retrieved_chunks)

    prompt = build_rag_prompt(question=request.question, context=context)

    start = perf_counter()

    answer = await generate_answer(prompt)

    print("llm : ", perf_counter() - start)

    used_chunks = [
        RetrievedChunkResponse.model_validate(chunk)
        for chunk in retrieved_chunks
    ]

    return QuestionResponse(
        question=request.question,
        answer=answer,
        retrieval_mode=request.retrieval_mode,
        used_chunks=used_chunks
    )


@router.post("/ask", response_model=QuestionResponse)
async def ask_all_documents(request: QuestionRequest, db: SessionDB) -> QuestionResponse:
    return await answer_question(
        request=request,
        db=db
    )


@router.post("/ask/{document_id}", response_model=QuestionResponse)
async def ask_one_document(document_id: int, request: QuestionRequest, db: SessionDB) -> QuestionResponse:
    await get_document_by_id(
        db=db,
        document_id=document_id
    )

    return await answer_question(
        request=request,
        db=db,
        document_id=document_id
    )