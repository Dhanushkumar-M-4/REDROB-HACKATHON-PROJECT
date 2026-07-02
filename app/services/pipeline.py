"""Pipeline orchestrator — ties all ranking components together."""

from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger
from rich.console import Console

from app.core.config import settings
from app.embeddings.embedding_service import EmbeddingService
from app.embeddings.vector_store import VectorStore
from app.models.candidate import CandidateCollection, CandidateProfile
from app.models.job import JobDescription, JobRequirements
from app.models.ranking import LLMEvaluation, RankedCandidate, RankingResult
from app.parsing.candidate_parser import CandidateParser
from app.parsing.jd_parser import JDParser
from app.ranking.hybrid_scorer import HybridScorer
from app.ranking.llm_ranker import LLMRanker
from app.ranking.semantic_ranker import SemanticRanker
from app.services.export_service import ExportService


class RankingPipeline:
    """End-to-end candidate ranking pipeline.

    Orchestrates the full ranking flow:
    1. Parse job description → extract requirements
    2. Parse candidate data → structured profiles
    3. Generate embeddings → build FAISS index
    4. Semantic search → retrieve top-k candidates
    5. LLM re-ranking → deep evaluation
    6. Hybrid scoring → final weighted scores
    7. Export results → CSV, JSON, console
    """

    def __init__(self):
        # ── Initialize Components ──────────────────────────────────
        self.candidate_parser = CandidateParser()
        self.jd_parser = JDParser(
            ollama_model=settings.ollama_model,
            ollama_timeout=settings.ollama_timeout,
        )
        self.embedding_service = EmbeddingService(
            primary_model=settings.primary_embedding_model,
            fallback_model=settings.fallback_embedding_model,
            batch_size=settings.embedding_batch_size,
        )
        self.vector_store: Optional[VectorStore] = None
        self.semantic_ranker: Optional[SemanticRanker] = None
        self.llm_ranker = LLMRanker(
            model=settings.ollama_model,
            timeout=settings.ollama_timeout,
            max_retries=settings.llm_max_retries,
        )
        self.hybrid_scorer = HybridScorer(
            weight_semantic=settings.weight_semantic,
            weight_llm=settings.weight_llm,
            weight_experience=settings.weight_experience,
            weight_skills=settings.weight_skills,
            weight_education=settings.weight_education,
        )
        self.export_service = ExportService(
            output_dir=str(settings.output_dir),
        )

        # ── State ──────────────────────────────────────────────────
        self.candidates: List[CandidateProfile] = []
        self.job_description: Optional[JobDescription] = None
        self.latest_result: Optional[RankingResult] = None

        logger.info("RankingPipeline initialized")

    def _init_vector_components(self) -> None:
        """Initialize vector store and semantic ranker after embedding model is loaded."""
        dimension = self.embedding_service.dimension
        self.vector_store = VectorStore(
            dimension=dimension,
            index_name=settings.faiss_index_name,
        )
        self.semantic_ranker = SemanticRanker(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

    def run(
        self,
        jd_source: Optional[str] = None,
        candidates_source: Optional[str] = None,
        export_csv: bool = True,
        export_json: bool = True,
        display_table: bool = True,
    ) -> RankingResult:
        """Execute the full ranking pipeline.

        Args:
            jd_source: Path to job description file, or raw text.
                       If None, uses default from data/job_descriptions/.
            candidates_source: Path to candidate data file/directory.
                               If None, uses default from data/candidates/.
            export_csv: Whether to export CSV.
            export_json: Whether to export JSON.
            display_table: Whether to display Rich console table.

        Returns:
            RankingResult with all ranked candidates.
        """
        logger.info("=" * 60)
        logger.info("STARTING RANKING PIPELINE")
        logger.info("=" * 60)

        # ── Step 1: Parse Job Description ──────────────────────────
        console = Console()
        with console.status("[bold cyan]Step 1/7 │ Parsing job description...[/bold cyan]") as status:
            logger.info("Step 1/7 │ Parsing job description")
        jd = self._load_job_description(jd_source)
        self.job_description = jd
        requirements = jd.requirements
        logger.info(
            "JD parsed │ role={} │ required_skills={} │ exp={}-{} years",
            requirements.role,
            len(requirements.required_skills),
            requirements.experience_min,
            requirements.experience_max,
        )

        # ── Step 2: Parse Candidates ───────────────────────────────
        with console.status("[bold cyan]Step 2/7 │ Parsing candidate data...[/bold cyan]"):
            logger.info("Step 2/7 │ Parsing candidate data")
        candidates = self._load_candidates(candidates_source)
        self.candidates = candidates
        logger.info("Candidates loaded │ total={}", len(candidates))

        if not candidates:
            logger.error("No candidates found. Pipeline cannot continue.")
            return RankingResult(job_role=requirements.role, total_candidates=0)

        # ── Step 3: Generate Embeddings & Build FAISS ──────────────
        with console.status("[bold cyan]Step 3/7 │ Generating embeddings and building FAISS index...[/bold cyan]"):
            logger.info("Step 3/7 │ Generating embeddings and building FAISS index")
        self._init_vector_components()
        self.semantic_ranker.build_index(candidates)

        # Save FAISS index
        self.vector_store.save(str(settings.vector_db_dir))

        # ── Step 4: Semantic Search ────────────────────────────────
        with console.status(f"[bold cyan]Step 4/7 │ Running semantic search (top {settings.faiss_top_k})...[/bold cyan]"):
            logger.info("Step 4/7 │ Running semantic search (top {})", settings.faiss_top_k)
        semantic_scores = self.semantic_ranker.get_scores_dict(
            requirements, top_k=settings.faiss_top_k
        )
        top_candidate_ids = list(semantic_scores.keys())
        logger.info("Semantic search retrieved {} candidates", len(top_candidate_ids))

        # Filter candidates to top-k for LLM evaluation
        top_candidates = [c for c in candidates if c.id in top_candidate_ids]

        # ── Step 5: LLM Re-ranking ─────────────────────────────────
        with console.status(f"[bold cyan]Step 5/7 │ LLM re-ranking ({len(top_candidates)} candidates)...[/bold cyan]"):
            logger.info("Step 5/7 │ LLM re-ranking ({} candidates)", len(top_candidates))
        llm_evaluations: Dict[str, LLMEvaluation] = {}

        if self.llm_ranker.is_available:
            llm_evaluations = self.llm_ranker.evaluate_batch(
                top_candidates, requirements
            )
        else:
            logger.warning("Ollama unavailable — skipping LLM re-ranking")
            for c in top_candidates:
                llm_evaluations[c.id] = LLMEvaluation(
                    reasoning="LLM evaluation unavailable"
                )

        # ── Step 6: Hybrid Scoring ─────────────────────────────────
        with console.status("[bold cyan]Step 6/7 │ Computing hybrid scores...[/bold cyan]"):
            logger.info("Step 6/7 │ Computing hybrid scores")
        ranked_candidates = self.hybrid_scorer.compute_scores(
            candidates=top_candidates,
            job_requirements=requirements,
            semantic_scores=semantic_scores,
            llm_evaluations=llm_evaluations,
        )

        # ── Step 7: Export Results ─────────────────────────────────
        logger.info("Step 7/7 │ Exporting results")

        result = RankingResult(
            job_role=requirements.role,
            total_candidates=len(ranked_candidates),
            ranked_candidates=ranked_candidates,
        )

        if export_csv:
            csv_path = self.export_service.export_csv(ranked_candidates)
            result.output_file = csv_path

        if export_json:
            self.export_service.export_json(result)

        if display_table:
            self.export_service.display_table(
                ranked_candidates,
                title=f"🏆 Ranking Results for: {requirements.role}",
            )

        self.latest_result = result

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE │ ranked {} candidates", len(ranked_candidates))
        logger.info("=" * 60)

        return result

    def rank_with_jd_text(
        self,
        jd_text: str,
        export_csv: bool = True,
        display_table: bool = True,
    ) -> RankingResult:
        """Run ranking pipeline with raw JD text (used by API).

        Args:
            jd_text: Raw job description text.
            export_csv: Whether to export CSV.
            display_table: Whether to show console table.

        Returns:
            RankingResult.
        """
        return self.run(
            jd_source=jd_text,
            export_csv=export_csv,
            export_json=True,
            display_table=display_table,
        )

    # ── Private Helpers ────────────────────────────────────────────

    def _load_job_description(self, source: Optional[str] = None) -> JobDescription:
        """Load and parse a job description."""
        if source is None:
            # Find first JD file in default directory
            jd_dir = settings.job_descriptions_dir
            jd_files = list(jd_dir.glob("*"))
            jd_files = [
                f for f in jd_files
                if f.suffix.lower() in settings.supported_jd_extensions
            ]
            if not jd_files:
                raise FileNotFoundError(
                    f"No job description files found in {jd_dir}"
                )
            source = str(jd_files[0])
            logger.info("Auto-detected JD file: {}", source)

        return self.jd_parser.parse(source)

    def _load_candidates(
        self, source: Optional[str] = None
    ) -> List[CandidateProfile]:
        """Load and parse candidate data."""
        if source is None:
            source = str(settings.candidates_dir)
            logger.info("Loading candidates from default directory: {}", source)

        source_path = Path(source)

        if source_path.is_dir():
            collection = self.candidate_parser.parse_directory(source_path)
        elif source_path.is_file():
            collection = self.candidate_parser.parse_file(source_path)
        else:
            raise FileNotFoundError(f"Candidate source not found: {source}")

        return collection.candidates

    def get_candidate(self, candidate_id: str) -> Optional[dict]:
        """Get a candidate's profile and ranking info.

        Args:
            candidate_id: The candidate's ID.

        Returns:
            Dict with candidate profile and scores, or None.
        """
        # Find candidate profile
        candidate = next(
            (c for c in self.candidates if c.id == candidate_id), None
        )
        if candidate is None:
            return None

        result = candidate.model_dump()

        # Add ranking info if available
        if self.latest_result:
            ranking = next(
                (r for r in self.latest_result.ranked_candidates
                 if r.candidate_id == candidate_id),
                None,
            )
            if ranking:
                result["ranking"] = ranking.model_dump()

        return result
