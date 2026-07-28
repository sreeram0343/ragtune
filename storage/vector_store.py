"""
RAGTUNE - Hybrid Vector & Sparse Document Store
Combines Dense Vector Cosine Similarity and Sparse BM25 Search via Reciprocal Rank Fusion (RRF).
"""

import math
import re
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from storage.document_processor import DocumentChunk


class HybridVectorStore:
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.chunks: List[DocumentChunk] = []
        self.chunk_map: Dict[str, DocumentChunk] = {}
        
        # Dense vectors matrix
        self.dense_vectors: List[np.ndarray] = []
        
        # Sparse BM25 index components
        self.doc_freqs: Dict[str, int] = {}
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.tokenized_corpus: List[List[str]] = []
        self.k1: float = 1.5
        self.b: float = 0.75

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25 indexing."""
        return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    def _generate_deterministic_embedding(self, text: str) -> np.ndarray:
        """
        Generates lightweight, reproducible dense vector representation.
        """
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        words = self._tokenize(text)
        if not words:
            return vec

        for word in words:
            # Deterministic hash mapping into vector dimensions
            h = hash(word)
            idx1 = abs(h) % self.embedding_dim
            idx2 = abs(hash(word[::-1])) % self.embedding_dim
            val = (h % 100) / 100.0
            vec[idx1] += val
            vec[idx2] += val * 0.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Adds DocumentChunk objects to both Dense and Sparse indices."""
        for chunk in chunks:
            if chunk.chunk_id in self.chunk_map:
                continue

            self.chunks.append(chunk)
            self.chunk_map[chunk.chunk_id] = chunk

            # Dense Vector Indexing
            emb = self._generate_deterministic_embedding(chunk.content)
            self.dense_vectors.append(emb)

            # Sparse BM25 Indexing
            tokens = self._tokenize(chunk.content)
            self.tokenized_corpus.append(tokens)

            # Track doc frequencies
            seen_tokens = set(tokens)
            for token in seen_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.corpus_size = len(self.chunks)
        if self.corpus_size > 0:
            total_len = sum(len(t) for t in self.tokenized_corpus)
            self.avg_doc_len = total_len / self.corpus_size

    def search_dense(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Dense Cosine Similarity Search."""
        if not self.chunks:
            return []

        query_vec = self._generate_deterministic_embedding(query)
        matrix = np.array(self.dense_vectors)
        
        # Cosine similarity (since vectors are normalized)
        similarities = np.dot(matrix, query_vec)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            results.append((self.chunks[idx], score))

        return results

    def search_sparse_bm25(self, query: str, top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """Sparse BM25 Search."""
        if not self.chunks or self.corpus_size == 0:
            return []

        query_tokens = self._tokenize(query)
        scores = np.zeros(self.corpus_size, dtype=np.float32)

        for token in query_tokens:
            if token not in self.doc_freqs:
                continue

            df = self.doc_freqs[token]
            idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

            for idx, doc_tokens in enumerate(self.tokenized_corpus):
                tf = doc_tokens.count(token)
                if tf == 0:
                    continue

                doc_len = len(doc_tokens)
                num = tf * (self.k1 + 1)
                den = tf + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                scores[idx] += idf * (num / den)

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0:
                results.append((self.chunks[idx], score))

        return results

    def search_hybrid(
        self, query: str, top_k: int = 5, rrf_k: float = 60.0
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Combines Dense and Sparse Search using Reciprocal Rank Fusion (RRF).
        RRF Score = 1 / (k + rank_dense) + 1 / (k + rank_sparse)
        """
        dense_hits = self.search_dense(query, top_k=top_k * 2)
        sparse_hits = self.search_sparse_bm25(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}

        # Rank dense
        for rank, (chunk, score) in enumerate(dense_hits, start=1):
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (rrf_k + rank))

        # Rank sparse
        for rank, (chunk, score) in enumerate(sparse_hits, start=1):
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (rrf_k + rank))

        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for chunk_id, rrf_score in sorted_chunks:
            results.append((self.chunk_map[chunk_id], float(rrf_score)))

        return results
