import keyword
from pathlib import Path
from typing import Any
import re

from backend.app.schemas import document
from backend.test_tool_selector import selected_tool
import chromadb


class VectorStoreService:

    def __init__(self):
        database_path = Path(__file__).resolve().parents[3] / "chroma_db"
        self.client = chromadb.PersistentClient(
            path=str(database_path)
        )

        self.collection = self.client.get_or_create_collection(
            name="research_documents"
        )

    def add_documents(
        self,
        chunks: list[str],
        embeddings: list[list[float]],
        document_id: str = "document"
    ):
        ids = [
            f"{document_id}_chunk_{index}"
            for index in range(len(chunks))
        ]

        self.collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings
        )

    def search(
        self, 
        query_embeddings: list[float],
        query_text: str,
        top_k: int = 3

    ) -> dict[str, list[list[Any]]]:
        total = self.collection.count()
        if self.collection.count()==0:
            return {"document": [[]]}

        semantic_results = self.collection.query(
            query_embeddings = [query_embeddings], n_results = top_k
        )

        keywords = set(
            re.findall(r"\b[\w-]+\b", query_text.lower())
        )

        stored = self.collection.get(
            include = ["documents", "metadatas"]

        )
        documents = stored.get("documents",[]) or []
        metadatas = stored.get("metadatas", []) or []

        ids = stored.get("ids",[]) or []

        keyword_matches = []

        for index, document in enumerate(documents):
            if not document:
                continue

            text=  document.lower()
            score = sum(
                len(re.findall(
                    rf"\b{re.escape(keyword)}\b",text
                ))
                for keyword in keywords
            )
            if score > 0:
                keyword_matches.sort(
                    key = lambda item: item[0],
                    reverse = True
                )
            semantic_ids = semantic_results["ids"][0]
            selected_indices = []

            for semantic_id in semantic_ids:
                if semantic_id in ids:
                    selected_indices.append(
                        ids.index(semantic_ids)
                    )
            for score, index in keyword_matches:
                if index not in selected_indices:
                    selected_indices.append(index)

                if len(selected_indices) >= top_k:
                    break

                selected_indices = selected_indices[:top_k]
                return{
                    "ids": [[ids[i] for i in selected_indices]],
                    "documents": [[documents[i] for i in selected_indices]],
                    "distancs": [[None for_in selected_indices]]
                }

      

        return results           