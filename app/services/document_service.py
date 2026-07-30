from typing import Any

from fastapi import HTTPException, status

from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.models.document import Document

from app.models.documentchunk import DocumentChunk


async def save_document_chunks(db: AsyncSession, filename: str, category: str, chunks: list[str], embeddings: Any) -> Document:
    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks must match to number of embeddings")

    document = Document(filename=filename, category=category)

    db.add(document)

    await db.flush()

    document_chunks: list[DocumentChunk] = []

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        document_chunk = DocumentChunk(
            document_id=document.id,
            text=str(chunk["text"]),
            page_number=int(chunk["page_number"]),
            chunk_index=int(chunk["chunk_index"]),
            embeddings=embedding
        )

        document_chunks.append(document_chunk)

    db.add_all(document_chunks)

    await db.commit()

    await db.refresh(document)

    return document


async def get_all_documents(db: AsyncSession) -> list[Document]:
    results = await db.execute(select(Document))

    return results.scalars().all()


async def get_document_by_id(document_id: int, db: AsyncSession) -> Document:
    result = await db.execute(select(Document).options(selectinload(Document.chunks)).where(Document.id == document_id))

    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found")

    return document


async def get_document_stats(document_id: int, db: AsyncSession) -> int:
    result = await db.execute(select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id==document_id))

    return int(result.scalar_one())


async def delete_document(db: AsyncSession, document_id: int) -> dict[str, int | str]:
    document = await get_document_by_id(db=db, document_id=document_id)

    await db.delete(document)

    await db.commit()

    return {
        "message": "Document was deleted",
        "document_id": document_id
    }