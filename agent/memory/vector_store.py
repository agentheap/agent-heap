from typing import Any

import chromadb


class AgentMemory:
    def __init__(self, path: str = "./chroma_data"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("agent_memory")

    def store_decision(self, decision: dict[str, Any]) -> None:
        doc_id = str(hash(str(decision)))
        text = str(decision)
        self.collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[decision],
        )

    def query_similar(self, context: str, k: int = 3) -> list[dict[str, Any]]:
        results = self.collection.query(query_texts=[context], n_results=k)
        if not results["metadatas"] or not results["metadatas"][0]:
            return []
        return [dict(m) for m in results["metadatas"][0]]
