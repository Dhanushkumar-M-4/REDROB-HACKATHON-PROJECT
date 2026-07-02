"""FAISS vector store for semantic search."""

from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger


class VectorStore:
    """FAISS-based vector store for fast similarity search.

    Supports building, searching, saving, and loading FAISS indices
    with cosine similarity (via inner product on L2-normalized vectors).
    """

    def __init__(self, dimension: int, index_name: str = "candidate_index"):
        """Initialize the vector store.

        Args:
            dimension: Embedding vector dimension.
            index_name: Name for saving/loading the index.
        """
        self.dimension = dimension
        self.index_name = index_name
        self._index: Optional[faiss.IndexFlatIP] = None
        self._id_mapping: List[str] = []  # Maps FAISS internal IDs to candidate IDs

    @property
    def index(self) -> faiss.IndexFlatIP:
        """Get or create the FAISS index."""
        if self._index is None:
            # Use Inner Product index (equivalent to cosine sim on normalized vectors)
            self._index = faiss.IndexFlatIP(self.dimension)
            logger.debug("Created new FAISS IndexFlatIP │ dimension={}", self.dimension)
        return self._index

    @property
    def size(self) -> int:
        """Return the number of vectors in the index."""
        return self.index.ntotal

    def build(
        self,
        embeddings: np.ndarray,
        candidate_ids: List[str],
    ) -> None:
        """Build the FAISS index from embeddings.

        Args:
            embeddings: numpy array of shape (n_candidates, dimension).
            candidate_ids: List of candidate IDs corresponding to each embedding.

        Raises:
            ValueError: If embeddings shape doesn't match dimension or IDs.
        """
        if embeddings.shape[0] != len(candidate_ids):
            raise ValueError(
                f"Mismatch: {embeddings.shape[0]} embeddings vs {len(candidate_ids)} IDs"
            )

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}"
            )

        # Ensure float32 for FAISS
        embeddings = embeddings.astype(np.float32)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        # Build index
        self._index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
        self._id_mapping = list(candidate_ids)

        logger.info(
            "FAISS index built │ vectors={} │ dimension={}",
            self.size,
            self.dimension,
        )

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 30,
    ) -> List[Tuple[str, float]]:
        """Search for the most similar candidates.

        Args:
            query_embedding: Query vector of shape (1, dimension) or (dimension,).
            top_k: Number of top results to return.

        Returns:
            List of (candidate_id, similarity_score) tuples, sorted by similarity.
        """
        if self.size == 0:
            logger.warning("FAISS index is empty, no results")
            return []

        # Reshape if needed
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        query_embedding = query_embedding.astype(np.float32)
        faiss.normalize_L2(query_embedding)

        # Limit top_k to index size
        k = min(top_k, self.size)

        # Search
        scores, indices = self.index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue
            candidate_id = self._id_mapping[idx]
            # Convert inner product to 0-100 score
            similarity = float(max(0, min(score, 1.0))) * 100
            results.append((candidate_id, similarity))

        logger.info("FAISS search │ top_k={} │ results={}", top_k, len(results))
        return results

    def save(self, save_dir: str) -> None:
        """Save the FAISS index and ID mapping to disk.

        Args:
            save_dir: Directory to save the index files.
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        index_path = save_path / f"{self.index_name}.faiss"
        mapping_path = save_path / f"{self.index_name}_ids.npy"

        faiss.write_index(self.index, str(index_path))
        np.save(str(mapping_path), np.array(self._id_mapping))

        logger.info(
            "FAISS index saved │ path={} │ vectors={}",
            index_path,
            self.size,
        )

    def load(self, save_dir: str) -> bool:
        """Load a FAISS index and ID mapping from disk.

        Args:
            save_dir: Directory containing the saved index files.

        Returns:
            True if loaded successfully, False otherwise.
        """
        save_path = Path(save_dir)
        index_path = save_path / f"{self.index_name}.faiss"
        mapping_path = save_path / f"{self.index_name}_ids.npy"

        if not index_path.exists() or not mapping_path.exists():
            logger.debug("No saved index found at {}", save_path)
            return False

        try:
            self._index = faiss.read_index(str(index_path))
            self._id_mapping = list(np.load(str(mapping_path), allow_pickle=True))

            # Verify dimension
            if self._index.d != self.dimension:
                logger.warning(
                    "Dimension mismatch │ expected={} │ loaded={}",
                    self.dimension,
                    self._index.d,
                )
                self._index = None
                self._id_mapping = []
                return False

            logger.info(
                "FAISS index loaded │ path={} │ vectors={}",
                index_path,
                self.size,
            )
            return True

        except Exception as e:
            logger.error("Failed to load FAISS index: {}", e)
            return False

    def reset(self) -> None:
        """Clear the index and ID mapping."""
        self._index = None
        self._id_mapping = []
        logger.debug("FAISS index reset")
