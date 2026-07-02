"""AI Smart Candidate Ranking System - Core Configuration."""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized application configuration."""

    # ── Project Paths ──────────────────────────────────────────────
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def candidates_dir(self) -> Path:
        return self.data_dir / "candidates"

    @property
    def job_descriptions_dir(self) -> Path:
        return self.data_dir / "job_descriptions"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "output"

    @property
    def vector_db_dir(self) -> Path:
        return self.project_root / "vector_db"

    # ── Embedding Configuration ────────────────────────────────────
    primary_embedding_model: str = "BAAI/bge-large-en-v1.5"
    fallback_embedding_model: str = "all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    embedding_dimension: int = 1024  # bge-large dimension; 384 for MiniLM

    # ── FAISS Configuration ────────────────────────────────────────
    faiss_index_name: str = "candidate_index"
    faiss_top_k: int = 30

    # ── Ollama / LLM Configuration ─────────────────────────────────
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout: int = 120  # seconds per request
    llm_max_retries: int = 2

    # ── Hybrid Scoring Weights ─────────────────────────────────────
    weight_semantic: float = 0.40
    weight_llm: float = 0.30
    weight_experience: float = 0.15
    weight_skills: float = 0.10
    weight_education: float = 0.05

    # ── FastAPI Configuration ──────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "AI Smart Candidate Ranking System"
    api_version: str = "1.0.0"
    api_description: str = (
        "Production-quality AI candidate ranking using semantic search and LLM re-ranking."
    )

    # ── Logging ────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "logs/ranking_system.log"

    # ── Supported File Extensions ──────────────────────────────────
    supported_candidate_extensions: List[str] = [".csv", ".json", ".txt", ".pdf", ".docx"]
    supported_jd_extensions: List[str] = [".txt", ".pdf", ".docx", ".json"]

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        dirs = [
            self.data_dir,
            self.candidates_dir,
            self.job_descriptions_dir,
            self.processed_dir,
            self.output_dir,
            self.vector_db_dir,
            self.project_root / "logs",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    model_config = {"env_prefix": "RANKING_", "extra": "ignore"}


# ── Singleton ──────────────────────────────────────────────────────
settings = Settings()
