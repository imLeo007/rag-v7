from sqlalchemy import Integer, DateTime, func, ForeignKey, UniqueConstraint, Text, Computed

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings

from pgvector.sqlalchemy import Vector

from sqlalchemy.dialects.postgresql import TSVECTOR

from datetime import datetime

from typing import Any

from app.core.database import Base

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.document import Document


class DocumentChunk(Base):
    __tablename__ = "documentchunks"

    __tabel_args__ = (
        UniqueConstraint(
            "chunk_index",
            "document_id",
            "page_number",
            name="uq_document_chunk_pos"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    embeddings: Mapped[Any] = mapped_column(
        Vector(settings.embedding_dimension),
        nullable=False
    )

    search_vector: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(text, ''))",
            persisted=True
        ),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks"
    )