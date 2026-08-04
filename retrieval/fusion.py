"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Reciprocal Rank Fusion (RRF)
Combines dense and sparse ranked candidate lists into a unified relevance score.
"""


from retrieval.domain import DocumentChunk, SearchCandidate


class ReciprocalRankFusion:
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def fuse(
        self,
        dense_candidates: list[SearchCandidate],
        sparse_candidates: list[SearchCandidate],
        top_k: int = 10,
    ) -> list[SearchCandidate]:
        """
        Applies Reciprocal Rank Fusion (RRF) formula:
        Score(chunk) = sum(1 / (k + rank_i))
        """
        scores: dict[str, float] = {}
        chunks_map: dict[str, DocumentChunk] = {}

        # 1. Process Dense Candidate Ranks
        for candidate in dense_candidates:
            cid = candidate.chunk.chunk_id
            chunks_map[cid] = candidate.chunk
            rrf_score = 1.0 / (self.rrf_k + candidate.rank)
            scores[cid] = scores.get(cid, 0.0) + rrf_score

        # 2. Process Sparse Candidate Ranks
        for candidate in sparse_candidates:
            cid = candidate.chunk.chunk_id
            chunks_map[cid] = candidate.chunk
            rrf_score = 1.0 / (self.rrf_k + candidate.rank)
            scores[cid] = scores.get(cid, 0.0) + rrf_score

        # 3. Sort Fused Results
        sorted_cids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        fused_results = []
        for rank, cid in enumerate(sorted_cids[:top_k], start=1):
            fused_results.append(
                SearchCandidate(
                    chunk=chunks_map[cid],
                    score=round(scores[cid], 6),
                    rank=rank,
                    source="FUSED",
                )
            )

        return fused_results
