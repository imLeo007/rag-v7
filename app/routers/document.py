import os

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chunker import chunk_pages

from app.ai.embedding import create_embeddings

from app.core.database import get_db

from app.services.document_service import get_all_documents, get_document_by_id, get_document_stats, delete_document, save_document_chunks

from app.schemas.document import DocumentDeleteResponse, DocumentResponse, DocumentDetailResponse, DocumentUploadResponse

from app.services.pdf_service import extract_pages_from_pdf, save_pdf


router = APIRouter(prefix="/document", tags=["Document"])


SessionDB = Annotated[AsyncSession, Depends(get_db)]


UPLOAD_DIRECTORY = "uploads"

# endpoints

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(db: SessionDB, category: str, file: Annotated[UploadFile, File(...)]) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document must have a filename.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document must be a pdf.")

    file_path: str | None = None

    try:
        file_path = save_pdf(file=file, upload_dir=UPLOAD_DIRECTORY)

        pages = extract_pages_from_pdf(file_path)

        if not pages:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Could not extract from pdf.")

        chunks = chunk_pages(pages=pages, chunk_size=200, overlap=50)

        if not chunks:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="No chunks could be created from pdf.")

        chunk_text = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = create_embeddings(chunk_text)

        document = await save_document_chunks(
            db=db,
            filename=file.filename,
            category=category,
            chunks=chunks,
            embeddings=embeddings
        )

        return DocumentUploadResponse(
            message="Document uploaded successfully",
            document_id=document.id,
            filename=document.filename,
            category=category,
            chunks_created=len(chunks)
        )


    finally:
        await file.close()

        if file_path and os.path.exists(file_path):
            os.remove(file_path)



@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: SessionDB) -> list[DocumentResponse]:

    documents = await get_all_documents(db=db)

    return [
        DocumentResponse.model_validate(document)
        for document in documents
    ]



@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(db: SessionDB, document_id: int) -> DocumentDetailResponse:
    document = await get_document_by_id(db=db, document_id=document_id)

    total_chunks = await get_document_stats(db=db, document_id=document_id)

    return DocumentDetailResponse(
        id=document.id,
        filename=document.filename,
        category=document.category,
        created_at=document.created_at,
        total_chunks=total_chunks
    )



@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def remove_document(db: SessionDB, document_id: int) -> DocumentDeleteResponse:
    result = await delete_document(db=db, document_id=document_id)

    return DocumentDeleteResponse(**result)