from datetime import datetime, timezone
from typing import Any

import chromadb

MEMORY_COLLECTION = "agent_memory"
DEFAULT_CHROMA_PATH = "./chroma_data"


class AgentMemory:
    """ChromaDB-backed vector memory for storing and recalling agent decisions."""

    def __init__(self, path: str | None = None):
        self.path = path or DEFAULT_CHROMA_PATH
        self.client = chromadb.PersistentClient(path=self.path)
        self.collection = self.client.get_or_create_collection(MEMORY_COLLECTION)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store_decision(self, decision: dict[str, Any]) -> str:
        """Store a single decision with an auto-generated timestamp."""
        doc_id = str(hash(str(decision)))
        text = str(decision)
        metadata = {
            **decision,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata],
        )
        return doc_id

    def store_decisions_batch(
        self, decisions: list[dict[str, Any]]
    ) -> list[str]:
        """Store multiple decisions in one batch call."""
        if not decisions:
            return []

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        now = datetime.now(timezone.utc).isoformat()
        for d in decisions:
            ids.append(str(hash(str(d))))
            documents.append(str(d))
            metadatas.append({**d, "timestamp": now})

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return ids

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query_similar(
        self, context: str, k: int = 3
    ) -> list[dict[str, Any]]:
        """Retrieve *k* past decisions similar to *context*."""
        try:
            results = self.collection.query(
                query_texts=[context], n_results=k
            )
        except Exception:
            return []

        if not results.get("metadatas") or not results["metadatas"][0]:
            return []
        return [dict(m) for m in results["metadatas"][0]]

    def query_similar_filtered(
        self,
        context: str,
        k: int = 3,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Like *query_similar* but applies a metadata filter.

        Example: ``query_similar_filtered("deposit", where={"protocol": "aave"})``
        """
        try:
            results = self.collection.query(
                query_texts=[context],
                n_results=k,
                where=where,
            )
        except Exception:
            return []

        if not results.get("metadatas") or not results["metadatas"][0]:
            return []
        return [dict(m) for m in results["metadatas"][0]]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the total number of stored memory entries."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics about the memory collection."""
        count = self.count()
        return {
            "collection": MEMORY_COLLECTION,
            "count": count,
            "path": self.path,
        }

    def clear(self) -> None:
        """Delete all entries in the memory collection."""
        try:
            count = self.count()
            if count:
                self.collection.delete(where={})
        except Exception:
            pass
