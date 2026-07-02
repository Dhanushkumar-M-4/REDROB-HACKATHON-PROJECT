"""Embedding service using Sentence Transformers."""

from typing import List, Optional, Union

import numpy as np
from loguru import logger


class EmbeddingService:
    """Generates text embeddings using Sentence Transformers.

    Tries the primary model (BAAI/bge-large-en-v1.5) first,
    falls back to all-MiniLM-L6-v2 if unavailable.
    """

    def __init__(
        self,
        primary_model: str = "BAAI/bge-large-en-v1.5",
        fallback_model: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
    ):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.batch_size = batch_size
        self._model = None
        self._model_name: Optional[str] = None
        self._dimension: Optional[int] = None

    @property
    def model(self):
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            self._load_model()
        return self._model

    @property
    def dimension(self) -> int:
        """Return the embedding dimension of the loaded model."""
        if self._dimension is None:
            self._load_model()
        return self._dimension

    @property
    def model_name(self) -> str:
        """Return the name of the loaded model."""
        if self._model_name is None:
            self._load_model()
        return self._model_name

    def _load_model(self) -> None:
        """Load the embedding model with fallback."""
        from sentence_transformers import SentenceTransformer

        # Try primary model
        try:
            logger.info("Loading primary embedding model: {}", self.primary_model)
            self._model = SentenceTransformer(self.primary_model)
            self._model_name = self.primary_model
            test_emb = self._model.encode(["test"], show_progress_bar=False)
            self._dimension = test_emb.shape[1]
            logger.info(
                "Primary model loaded │ model={} │ dimension={}",
                self._model_name,
                self._dimension,
            )
            return
        except Exception as e:
            logger.warning("Primary model failed: {} │ Trying fallback...", e)

        # Try fallback model
        try:
            logger.info("Loading fallback embedding model: {}", self.fallback_model)
            self._model = SentenceTransformer(self.fallback_model)
            self._model_name = self.fallback_model
            test_emb = self._model.encode(["test"], show_progress_bar=False)
            self._dimension = test_emb.shape[1]
            logger.info(
                "Fallback model loaded │ model={} │ dimension={}",
                self._model_name,
                self._dimension,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load both embedding models. "
                f"Primary: {self.primary_model}, Fallback: {self.fallback_model}. "
                f"Error: {e}"
            )

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        show_progress: bool = True,
    ) -> np.ndarray:
        """Encode text(s) into embeddings.

        Args:
            texts: Single text or list of texts to encode.
            normalize: Whether to L2-normalize embeddings (required for cosine similarity).
            show_progress: Whether to show progress bar for batch encoding.

        Returns:
            numpy array of shape (n_texts, dimension).
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.array([]).reshape(0, self.dimension)

        logger.info("Encoding {} texts │ model={}", len(texts), self.model_name)

        # Add instruction prefix for BGE models
        if "bge" in self.model_name.lower():
            texts = [f"Represent this document for retrieval: {t}" for t in texts]

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress and len(texts) > 5,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )

        logger.debug("Encoded │ shape={}", embeddings.shape)
        return embeddings

    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """Encode a query text (uses query-specific prefix for BGE models).

        Args:
            query: Query text to encode.
            normalize: Whether to L2-normalize.

        Returns:
            numpy array of shape (1, dimension).
        """
        # BGE models use a different prefix for queries
        if "bge" in self.model_name.lower():
            query = f"Represent this sentence for searching relevant passages: {query}"

        embedding = self.model.encode(
            [query],
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embedding

    def compute_similarity(
        self,
        embedding_a: np.ndarray,
        embedding_b: np.ndarray,
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding_a: First embedding vector.
            embedding_b: Second embedding vector.

        Returns:
            Cosine similarity score (0 to 1 if normalized).
        """
        a = embedding_a.flatten()
        b = embedding_b.flatten()
        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
        return float(similarity)
