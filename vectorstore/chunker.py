"""Document chunking utilities for the vector store."""

from __future__ import annotations

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[str]:
    """Split text into overlapping chunks using recursive character splitting."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or config.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def chunk_documents(
    documents: List[dict],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> tuple[List[str], List[dict]]:
    """Chunk a list of {'text': ..., 'metadata': ...} dicts.

    Returns (chunks, metadatas) aligned by index.
    """
    all_chunks: List[str] = []
    all_metas: List[dict] = []

    for doc in documents:
        text = doc.get("text", "")
        meta = doc.get("metadata", {})
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metas.append({**meta, "chunk_index": i, "total_chunks": len(chunks)})

    return all_chunks, all_metas
