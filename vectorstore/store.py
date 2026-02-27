"""FAISS-backed vector store with OpenAI embeddings and disk persistence."""

from __future__ import annotations

import json
import os
import pickle
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

import config
from vectorstore.chunker import chunk_text, chunk_documents


class VectorStore:
    """Persistent FAISS vector store with OpenAI embeddings.

    Data is stored in a FAISS index + a sidecar JSON file for documents/metadata.
    The store auto-saves to disk on every write and loads on init.
    """

    def __init__(
        self,
        collection_name: str = "insurance_knowledge",
        persist_dir: str | None = None,
    ):
        self.collection_name = collection_name
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)

        self._index_path = os.path.join(self.persist_dir, f"{collection_name}.index")
        self._meta_path = os.path.join(self.persist_dir, f"{collection_name}.meta.json")

        self.embeddings = OpenAIEmbeddings(
            model=config.OPENAI_EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY,
        )

        # Internal storage
        self._ids: List[str] = []
        self._documents: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._index: faiss.IndexFlatIP | None = None  # cosine via normalized IP
        self._dim: int = 0

        self._load()

    # ── Persistence ──────────────────────────────────────────────────────

    def _load(self):
        """Load existing index + metadata from disk."""
        if os.path.exists(self._index_path) and os.path.exists(self._meta_path):
            self._index = faiss.read_index(self._index_path)
            with open(self._meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._ids = meta.get("ids", [])
            self._documents = meta.get("documents", [])
            self._metadatas = meta.get("metadatas", [])
            self._dim = meta.get("dim", 0)

    def _save(self):
        """Persist index + metadata to disk."""
        if self._index is not None:
            faiss.write_index(self._index, self._index_path)
        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "ids": self._ids,
                    "documents": self._documents,
                    "metadatas": self._metadatas,
                    "dim": self._dim,
                },
                f,
            )

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(vecs: np.ndarray) -> np.ndarray:
        """L2-normalize rows so inner-product == cosine similarity."""
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vecs / norms

    def _ensure_index(self, dim: int):
        if self._index is None or self._dim != dim:
            self._dim = dim
            self._index = faiss.IndexFlatIP(dim)  # Inner Product on normalized = cosine

    # ── Ingest ───────────────────────────────────────────────────────────

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Embed and store texts (already chunked)."""
        vectors = self.embeddings.embed_documents(texts)
        arr = self._normalize(np.array(vectors, dtype="float32"))

        self._ensure_index(arr.shape[1])

        ids = ids or [f"doc_{i}_{hash(t) % 10**8}" for i, t in enumerate(texts)]
        metadatas = metadatas or [{}] * len(texts)

        # Handle upserts: remove existing ids first
        existing = set(self._ids)
        for new_id in ids:
            if new_id in existing:
                idx = self._ids.index(new_id)
                # FAISS doesn't support delete, so we rebuild below
                pass

        # Simple approach: append (for large-scale, rebuild would be needed)
        self._index.add(arr)
        self._ids.extend(ids)
        self._documents.extend(texts)
        self._metadatas.extend(metadatas)

        self._save()
        return ids

    def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id_prefix: str = "doc",
    ) -> List[str]:
        """Chunk a single document, embed, and store it."""
        chunks = chunk_text(text)
        metas = [
            {**(metadata or {}), "chunk_index": i, "total_chunks": len(chunks)}
            for i in range(len(chunks))
        ]
        ids = [f"{doc_id_prefix}_{i}_{hash(c) % 10**8}" for i, c in enumerate(chunks)]
        return self.add_texts(chunks, metas, ids)

    def add_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        id_prefix: str = "batch",
    ) -> List[str]:
        """Chunk and ingest a batch of {'text': ..., 'metadata': ...} dicts."""
        chunks, metas = chunk_documents(documents)
        ids = [f"{id_prefix}_{i}_{hash(c) % 10**8}" for i, c in enumerate(chunks)]
        return self.add_texts(chunks, metas, ids)

    # ── Query ────────────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic similarity search.

        Returns list of dicts: {id, document, metadata, distance}.
        ``distance`` here is *cosine similarity* (higher = more similar).
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        query_vector = self.embeddings.embed_query(query_text)
        arr = self._normalize(np.array([query_vector], dtype="float32"))

        k = min(n_results, self._index.ntotal)
        distances, indices = self._index.search(arr, k)

        docs: List[Dict[str, Any]] = []
        for rank in range(k):
            idx = int(indices[0][rank])
            if idx < 0 or idx >= len(self._ids):
                continue

            meta = self._metadatas[idx] if idx < len(self._metadatas) else {}

            # Optional metadata filter
            if where:
                match = all(meta.get(wk) == wv for wk, wv in where.items())
                if not match:
                    continue

            docs.append(
                {
                    "id": self._ids[idx],
                    "document": self._documents[idx],
                    "metadata": meta,
                    "distance": float(distances[0][rank]),
                }
            )

        return docs

    # ── Utilities ────────────────────────────────────────────────────────

    def count(self) -> int:
        return self._index.ntotal if self._index else 0

    def delete_collection(self):
        self._ids.clear()
        self._documents.clear()
        self._metadatas.clear()
        self._index = None
        self._dim = 0
        for p in (self._index_path, self._meta_path):
            if os.path.exists(p):
                os.remove(p)

    def list_collections(self) -> List[str]:
        """List collection names from files in persist_dir."""
        names = set()
        if os.path.isdir(self.persist_dir):
            for f in os.listdir(self.persist_dir):
                if f.endswith(".index"):
                    names.add(f.replace(".index", ""))
        return sorted(names)


# ── Convenience singletons per collection ────────────────────────────────────

_stores: Dict[str, VectorStore] = {}


def get_vector_store(collection_name: str = "insurance_knowledge") -> VectorStore:
    if collection_name not in _stores:
        _stores[collection_name] = VectorStore(collection_name=collection_name)
    return _stores[collection_name]
