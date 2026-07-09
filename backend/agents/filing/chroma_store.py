"""ChromaDB helpers for the filing agent."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from backend.agents.langchain_utils import embedding_dimension

logger = logging.getLogger(__name__)


def reset_chroma_store(persist_dir: str) -> None:
    """Delete a stale Chroma persist directory so collections can be recreated."""
    path = Path(persist_dir)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
        logger.warning("Removed stale ChromaDB data at %s", path)


def create_vector_store(
    collection_name: str,
    persist_dir: str,
    embedding_model: Any,
) -> Any:
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_dir,
    )


def initialize_vector_store(
    collection_name: str,
    persist_dir: str,
    embedding_model: Any,
) -> Any:
    """Create Chroma, resetting persisted data when embedding dimensions changed."""
    expected_dim = embedding_dimension(embedding_model)

    try:
        vector_store = create_vector_store(collection_name, persist_dir, embedding_model)
        collection = getattr(vector_store, "_collection", None)
        if collection is not None and collection.count() > 0:
            stored_dim = collection.metadata.get("embedding_dimension")
            if stored_dim is None:
                try:
                    sample = collection.get(limit=1, include=["embeddings"])
                    embeddings = sample.get("embeddings") or []
                    if embeddings and embeddings[0] is not None:
                        stored_dim = len(embeddings[0])
                except Exception:
                    stored_dim = None
            if stored_dim is not None and int(stored_dim) != expected_dim:
                logger.warning(
                    "ChromaDB dimension mismatch (%s vs %s); recreating collection.",
                    stored_dim,
                    expected_dim,
                )
                reset_chroma_store(persist_dir)
                vector_store = create_vector_store(collection_name, persist_dir, embedding_model)
                collection = getattr(vector_store, "_collection", None)

        if collection is not None:
            collection.modify(metadata={"embedding_dimension": expected_dim})
        return vector_store
    except Exception as exc:
        if "dimension" not in str(exc).lower():
            raise
        logger.warning("ChromaDB dimension error during init; recreating store: %s", exc)
        reset_chroma_store(persist_dir)
        vector_store = create_vector_store(collection_name, persist_dir, embedding_model)
        collection = getattr(vector_store, "_collection", None)
        if collection is not None:
            collection.modify(metadata={"embedding_dimension": expected_dim})
        return vector_store


def recreate_vector_store(
    collection_name: str,
    persist_dir: str,
    embedding_model: Any,
) -> Any:
    """Force-recreate the vector store after a dimension mismatch at write time."""
    reset_chroma_store(persist_dir)
    vector_store = create_vector_store(collection_name, persist_dir, embedding_model)
    collection = getattr(vector_store, "_collection", None)
    if collection is not None:
        collection.modify(metadata={"embedding_dimension": embedding_dimension(embedding_model)})
    return vector_store
