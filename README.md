# RAG From Scratch — Version 7

A clean, modular RAG backend built from first principles.

This project is part of an ongoing learning series where each version adds **one meaningful improvement** without changing everything at once. The goal is simple: understand how retrieval systems actually work under the hood before relying on orchestration frameworks.

Version 7 focuses on making retrieval **more controlled, more relevant, and easier to reason about**.

---

## Why I Built This

Many people start building RAG systems with high-level frameworks. That is useful, but it can also hide the decisions that actually shape answer quality.

I wanted to understand the full path myself:

- how documents are processed
- how information is stored
- how relevant text is found
- how results are ranked
- how the final answer is grounded in the source

So instead of hiding the pipeline behind abstractions, I built it step by step.

The goal is **not** to avoid frameworks forever.  
The goal is to understand the system well enough to use them with confidence later.

---

## What Version 7 Improves

Version 7 keeps the earlier RAG pipeline and adds a few focused improvements:

- **Hybrid retrieval** to combine semantic search and keyword search
- **Reranking** to improve the final ordering of retrieved chunks
- **Metadata filtering** to keep search focused on the right document category
- **Centralized configuration** for cleaner setup and validation
- **Reranker preloading** so the model is loaded at startup instead of during the first request

This version is about improving **control, clarity, and answer quality** without changing the whole architecture.

---

## Pipeline

> Replace the image path below with the clean pipeline image for V7 in the next step.

![V7 RAG Pipeline](/screenshots/rag_v7_pipeline.png)

---

## How It Works

### 1) Document ingestion
A PDF is uploaded and its text is extracted.

### 2) Cleaning and chunking
The text is cleaned and split into smaller chunks so it can be searched effectively.

### 3) Indexing and storage
Each chunk is stored with:
- the original text
- its embedding
- searchable metadata

### 4) Question retrieval
When a user asks a question, the system searches in two ways:
- **semantic search** for meaning
- **keyword search** for exact terms

### 5) Hybrid fusion and reranking
The system merges both retrieval results, then reranks them so the most relevant chunks rise to the top.

### 6) Grounded answer generation
The best retrieved chunks are passed into the prompt, and the model answers using only that context.

---

## Why This Version Matters

A good RAG system is not just about calling a model.  
It is about building a strong information pipeline.

Version 7 reinforced a few important ideas for me:

- better retrieval leads to better answers
- exact terms and semantic meaning both matter
- ranking quality matters after retrieval
- metadata should be applied early, not after the search is done
- performance problems should be measured, not guessed

This version helped me move from **“it works”** to **“I understand why it works.”**

---

## Main Capabilities

- Upload PDF documents with category metadata
- Store document content for later retrieval
- Ask questions across all documents
- Ask questions within a specific document
- Filter retrieval by category
- Use vector, keyword, or hybrid retrieval
- Return grounded answers with source information
- Run the whole project in Docker

---

## Project Structure

```text
app/
├── ai/
│   ├── embeddings.py
│   ├── llm.py
│   ├── prompts.py
│   ├── reranker.py
│   └── retriever.py
├── core/
│   └── config.py
├── database/
│   └── database.py
├── models/
│   ├── document.py
│   └── document_chunk.py
├── routers/
│   ├── document.py
│   └── question.py
├── schemas/
│   ├── document.py
│   └── question.py
├── services/
│   ├── document_service.py
│   └── pdf_service.py
└── main.py
```

The structure is intentionally modular so each stage of the pipeline can be understood and debugged independently.

---

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/imLeo007/rag-from-scratch-v7.git
cd rag-from-scratch-v7
```

### 2. Create the environment file

Create a `.env` file based on your project settings.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/rag_v7_db

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

RERANKER_MODEL_NAME=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANK_CANDIDATE_K=10

GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini/gemini-2.0-flash
PORT=8000
```

### 3. Start the services

```bash
docker compose up --build
```

### 4. Run database migrations

```bash
docker compose exec api alembic upgrade head
```

### 5. Open the API docs

```text
http://localhost:8000/docs
```

---

## Example Request

```json
{
  "question": "What is machine learning?",
  "category": "AI",
  "top_k": 3,
  "retrieval_mode": "hybrid"
}
```

---

## Current Scope

This version currently supports **plain-text PDFs**.

That choice is intentional.

The main goal of this repository is to learn the core ideas behind retrieval, ranking, and grounded generation. More advanced extraction problems like OCR, scanned files, tables, and layout-heavy documents can come later.

---

## What This Project Demonstrates

This repository demonstrates:

- building a RAG system from scratch
- designing a modular AI backend
- combining two retrieval styles in one pipeline
- improving relevance through reranking
- controlling retrieval through metadata filtering
- keeping answers grounded in retrieved context
- measuring and improving the system step by step

---

## Version Progression

| Version | Focus |
|---|---|
| V4 | Built the base RAG pipeline from scratch |
| V5 | Added hybrid retrieval |
| V6 | Added reranking |
| **V7** | Added metadata filtering, cleaner configuration, and reranker preloading |

Each version is designed to introduce one major idea at a time so the improvement can be understood clearly.

---

## What Comes Next

The next versions will continue improving retrieval quality and context quality before moving toward more advanced AI workflows.

Planned future directions:

- parent-child retrieval
- context compression
- retrieval evaluation
- conversation memory
- more production-grade AI backend patterns
- eventually agent workflows

---

## Final Note

This project is part of my journey from backend development into AI backend engineering.

I am building these versions one step at a time so I can understand the architecture, logic, and tradeoffs behind each layer of a real RAG system.

If you are also learning RAG, I hope this repository helps you see that a strong system starts with a strong pipeline — not just a model call.

---

## License

This project is available under the [MIT License](LICENSE).
