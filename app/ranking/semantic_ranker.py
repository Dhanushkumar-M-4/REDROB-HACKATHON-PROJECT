"""Semantic ranker — retrieves top candidates via FAISS similarity search."""

from typing import Dict, List, Tuple

from loguru import logger

from app.embeddings.embedding_service import EmbeddingService
from app.embeddings.vector_store import VectorStore
from app.models.candidate import CandidateProfile
from app.models.job import JobRequirements


class SemanticRanker:
    """Retrieves top-k candidates based on semantic similarity to job requirements.

    Uses the embedding service to encode the JD and candidates,
    then performs FAISS similarity search.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def build_index(self, candidates: List[CandidateProfile]) -> None:
        """Build the FAISS index from candidate profiles.

        Args:
            candidates: List of parsed candidate profiles.
        """
        logger.info("Building FAISS index for {} candidates", len(candidates))

        # Generate embedding texts
        texts = [c.to_embedding_text() for c in candidates]
        ids = [c.id for c in candidates]

        # Encode all candidates
        embeddings = self.embedding_service.encode(texts, normalize=True)

        # Build FAISS index
        self.vector_store.build(embeddings, ids)

        logger.info("FAISS index ready │ vectors={}", self.vector_store.size)

    def search(
        self,
        job_requirements: JobRequirements,
        top_k: int = 30,
    ) -> List[Tuple[str, float]]:
        """Search for top-k candidates matching the job requirements.

        Args:
            job_requirements: Structured job requirements.
            top_k: Number of candidates to retrieve.

        Returns:
            List of (candidate_id, similarity_score) tuples.
        """
        # Encode job requirements as query
        query_text = job_requirements.to_embedding_text()
        logger.info("Encoding JD query for semantic search │ top_k={}", top_k)

        query_embedding = self.embedding_service.encode_query(query_text)

        # Search FAISS
        results = self.vector_store.search(query_embedding, top_k=top_k)

        logger.info(
            "Semantic search complete │ results={} │ top_score={:.2f} │ min_score={:.2f}",
            len(results),
            results[0][1] if results else 0,
            results[-1][1] if results else 0,
        )

        return results

    def get_scores_dict(
        self,
        job_requirements: JobRequirements,
        top_k: int = 30,
    ) -> Dict[str, float]:
        """Get semantic scores as a dictionary.

        Args:
            job_requirements: Structured job requirements.
            top_k: Number of candidates to retrieve.

        Returns:
            Dict mapping candidate_id → semantic_score (0-100).
        """
        results = self.search(job_requirements, top_k)
        return {cid: score for cid, score in results}
