import re

from typing import TypedDict


class ExtractedPage(TypedDict):
    page_number: int
    text: str

class TextChunk(TypedDict):
    text: str
    page_number: int
    chunk_index: int


def chunk_text(
        text: str,
        chunk_size: int = 200,
        overlap: int = 50
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap must be greater than zero")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    if not text or not text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks: list[str] = []
    current_words: list[str] = []

    for sentence in sentences:
        sentence_words = sentence.strip().split()

        if not sentence_words:
            continue

        if len(sentence_words) > chunk_size:
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = []

            step = chunk_size - overlap

            for start in range(0, len(sentence_words), step):
                piece = sentence_words[start: start + sentence_words]

                if piece:
                    chunks.append(" ".join(piece))

            continue

        if len(sentence_words) + len(current_words) > chunk_size:
            chunks.append(" ".join(current_words))

            overlap_words = current_words[-overlap:] if overlap else []

            max_overlap = chunk_size - len(sentence_words)

            current_words = overlap_words[-max_overlap:] if max_overlap > 0 else []

        current_words.extend(sentence_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def chunk_pages(pages: list[ExtractedPage], chunk_size: int = 200, overlap: int = 50) -> list[TextChunk]:
    all_chunks: list[TextChunk] = []

    for page in pages:
        page_chunks = chunk_text(
            text=page["text"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk_index, chunk in enumerate(page_chunks, start=1):
            all_chunks.append(
                {
                    "text": chunk,
                    "page_number": page["page_number"],
                    "chunk_index": chunk_index
                }
            )

    return all_chunks