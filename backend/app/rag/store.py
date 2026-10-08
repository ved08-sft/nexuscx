import chromadb
from fastembed import TextEmbedding
from typing import List, Tuple, Optional
import numpy as np
import hashlib
from app.schemas.rag import RagSearchResult, RagQueryResponse, RagQueryRequest
from app.schemas.enums import Vertical


class MiniLMEmbedder:
    """Wrapper for FastEmbed's MiniLM embedding model."""

    def __init__(self):
        self.model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    def __call__(self, input: List[str]) -> List[List[float]]:
        # FastEmbed returns a generator, convert to list of lists
        return [list(vec) for vec in self.model.embed(input)]

    def name(self) -> str:
        """Return the name of the embedding function."""
        return "sentence-transformers/all-MiniLM-L6-v2"

    def embed_query(self, input: List[str]) -> List[List[float]]:
        """Embed a query (alias for __call__ for ChromaDB compatibility)."""
        return self.__call__(input)


class SopStore:
    """Handles SOP storage and retrieval using ChromaDB."""

    def __init__(self, persist_directory: str = "/data/chroma"):
        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name="sops",
            embedding_function=MiniLMEmbedder(),
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize BM25 for sparse search
        try:
            from rank_bm25 import BM25Okapi
            self.bm25 = None  # Will be initialized when we add documents
            self.bm25_corpus = []  # Raw text for BM25
            self.bm25_mapping = {}  # Maps BM25 index to chunk_id
        except ImportError:
            self.bm25 = None

    def upsert_chunks(self, chunks: List[dict]) -> int:
        """
        Insert or update SOP chunks in the vector store.
        Each chunk should have: id, text, source, page, vertical, sop_version, section_title
        Returns number of chunks upserted.
        """
        if not chunks:
            return 0

        # Prepare data for ChromaDB
        ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        metadatas = []

        for chunk in chunks:
            metadata = {
                "source": chunk["source"],
                "page": chunk["page"],
                "vertical": chunk["vertical"],
                "sop_version": chunk.get("sop_version", "v1"),
                "section_title": chunk.get("section_title", "")
            }
            metadatas.append(metadata)

            # Also collect for BM25 if available
            if self.bm25 is not None:
                self.bm25_corpus.append(chunk["text"])
                self.bm25_mapping[len(self.bm25_corpus) - 1] = chunk["id"]

        # Upsert to ChromaDB (this will generate embeddings via our embedding function)
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

        # Re-initialize BM25 if we have a corpus
        if self.bm25 is not None and self.bm25_corpus:
            tokenized_corpus = [doc.lower().split() for doc in self.bm25_corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)

        return len(chunks)

    def search(self, query: str, vertical: Optional[Vertical] = None,
               top_k: int = 3) -> Tuple[List[RagSearchResult], float]:
        """
        Perform hybrid search (dense + sparse) and return results with confidence score.
        Returns: (results, confidence_score)
        """
        if not query.strip():
            return [], 0.0

        # Dense search using ChromaDB
        where_filter = {"vertical": vertical} if vertical else None

        dense_results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 2,  # Get extra for re-ranking after fusion
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        # Process dense results
        dense_docs = []
        if dense_results["ids"] and len(dense_results["ids"][0]) > 0:
            for i, doc_id in enumerate(dense_results["ids"][0]):
                # Convert distance to similarity score (chromadb returns distances)
                distance = dense_results["distances"][0][i]
                # For cosine distance, similarity = 1 - distance
                dense_score = max(0.0, min(1.0, 1.0 - distance))

                metadata = dense_results["metadatas"][0][i]
                dense_docs.append({
                    "id": doc_id,
                    "text": dense_results["documents"][0][i],
                    "metadata": metadata,
                    "dense_score": dense_score,
                    "index": i  # Keep track of original order
                })

        # Sparse search using BM25 (if available)
        sparse_scores = {}
        if self.bm25 is not None and len(self.bm25_corpus) > 0:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25.get_scores(tokenized_query)

            # Map BM25 scores back to chunk IDs
            for idx, score in enumerate(bm25_scores):
                if idx in self.bm25_mapping and score > 0:
                    chunk_id = self.bm25_mapping[idx]
                    sparse_scores[chunk_id] = score

        # Normalize sparse scores to 0-1 range
        if sparse_scores:
            max_sparse = max(sparse_scores.values()) if sparse_scores else 1.0
            if max_sparse > 0:
                sparse_scores = {k: v / max_sparse for k, v in sparse_scores.items()}

        # Combine scores using Reciprocal Rank Fusion (RRF)
        # RRF score = Σ 1/(k + rank_i) where k is typically 60
        K = 60
        fused_scores = {}

        # Rank dense results
        dense_ranked = sorted(dense_docs, key=lambda x: x["dense_score"], reverse=True)
        for rank, doc in enumerate(dense_ranked):
            chunk_id = doc["id"]
            if chunk_id not in fused_scores:
                fused_scores[chunk_id] = 0.0
            fused_scores[chunk_id] += 1.0 / (K + rank + 1)

        # Rank sparse results
        if sparse_scores:
            sparse_ranked = sorted(sparse_scores.items(), key=lambda x: x[1], reverse=True)
            for rank, (chunk_id, score) in enumerate(sparse_ranked):
                if chunk_id not in fused_scores:
                    fused_scores[chunk_id] = 0.0
                fused_scores[chunk_id] += 1.0 / (K + rank + 1)

        # Sort by fused score and take top_k
        ranked_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Build final results
        final_results = []
        for chunk_id, fused_score in ranked_results:
            # Find the document details
            doc_info = None
            for doc in dense_docs:
                if doc["id"] == chunk_id:
                    doc_info = doc
                    break

            if doc_info:
                metadata = doc_info["metadata"]
                result = RagSearchResult(
                    chunk_id=chunk_id,
                    text=doc_info["text"],
                    source=metadata["source"],
                    page=metadata["page"],
                    section_title=metadata.get("section_title"),
                    vertical=metadata["vertical"],
                    sop_version=metadata.get("sop_version", "v1"),
                    dense_score=doc_info["dense_score"],
                    sparse_score=sparse_scores.get(chunk_id, 0.0),
                    fused_score=fused_score,
                    score=fused_score  # Using fused score as the main score for now
                )
                final_results.append(result)

        # Calculate confidence score as the score of the top result
        confidence = final_results[0].score if final_results else 0.0

        return final_results, confidence

    def count(self) -> int:
        """Return the number of chunks in the collection."""
        return self.collection.count()

    def clear(self):
        """Delete all chunks from the collection."""
        self.client.delete_collection(name="sops")
        self.collection = self.client.get_or_create_collection(
            name="sops",
            embedding_function=MiniLMEmbedder(),
            metadata={"hnsw:space": "cosine"}
        )
        # Reset BM25
        self.bm25 = None
        self.bm25_corpus = []
        self.bm25_mapping = {}


# Global store instance
sop_store = SopStore()


def search_sops(query: str, vertical: Optional[str] = None,
                top_k: int = 3) -> Tuple[List[RagSearchResult], float]:
    """
    Convenience function for searching SOPs.
    Takes vertical as string for easier use in agents.
    """
    # Convert string vertical to enum if provided
    vertical_enum = None
    if vertical:
        try:
            vertical_enum = Vertical(vertical)
        except ValueError:
            # If vertical is not valid, ignore it
            pass

    results, confidence = sop_store.search(query, vertical=vertical_enum, top_k=top_k)
    return results, confidence


def upsert_sop_chunks(chunks: List[dict]) -> int:
    """Convenience function for upserting SOP chunks."""
    return sop_store.upsert_chunks(chunks)