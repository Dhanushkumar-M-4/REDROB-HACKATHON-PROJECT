"""LLM re-ranker — evaluates candidates using Ollama for deep assessment."""

import json
import re
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from app.models.candidate import CandidateProfile
from app.models.job import JobRequirements
from app.models.ranking import LLMEvaluation
from app.prompts.templates import PromptTemplates
from app.utils.text_utils import extract_json_from_llm_response


class LLMRanker:
    """Re-ranks candidates using Ollama LLM for nuanced evaluation.

    Evaluates each candidate across 8 dimensions:
    - Technical Skill Match
    - Relevant Experience
    - Project Relevance
    - Education
    - Career Growth
    - Communication
    - Leadership
    - Overall Fit
    """

    def __init__(
        self,
        model: str = "llama3",
        timeout: int = 120,
        max_retries: int = 2,
    ):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._available: Optional[bool] = None

    @property
    def is_available(self) -> bool:
        """Check if Ollama is available and the model is loaded."""
        if self._available is None:
            self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """Verify Ollama connectivity and model availability."""
        try:
            import ollama

            response = ollama.list()

            # Handle both old and new ollama API formats
            model_names = []
            # New API: response has .models attribute with model objects
            if hasattr(response, "models"):
                for m in response.models:
                    name = getattr(m, "model", None) or getattr(m, "name", "")
                    model_names.append(str(name))
            # Old API: response is a dict with 'models' key containing dicts
            elif isinstance(response, dict):
                for m in response.get("models", []):
                    if isinstance(m, dict):
                        name = m.get("name", m.get("model", ""))
                    else:
                        name = getattr(m, "model", None) or getattr(m, "name", "")
                    model_names.append(str(name))

            # Check if our model is available (handle tags like "llama3:latest")
            available = any(
                self.model in name or name.startswith(self.model)
                for name in model_names
            )
            if available:
                logger.info("Ollama available │ model={}", self.model)
            else:
                logger.warning(
                    "Ollama running but model '{}' not found │ available={}",
                    self.model,
                    model_names,
                )
            return available
        except ImportError:
            logger.warning("Ollama package not installed")
            return False
        except Exception as e:
            logger.warning("Ollama not available: {}", e)
            return False

    def evaluate_candidate(
        self,
        candidate: CandidateProfile,
        job_requirements: JobRequirements,
    ) -> LLMEvaluation:
        """Evaluate a single candidate using the LLM.

        Args:
            candidate: Candidate profile to evaluate.
            job_requirements: Job requirements for comparison.

        Returns:
            LLMEvaluation with scores and reasoning.
        """
        if not self.is_available:
            logger.debug("LLM unavailable, returning default evaluation for {}", candidate.id)
            return LLMEvaluation(reasoning="LLM evaluation unavailable")

        prompt = PromptTemplates.candidate_evaluation(
            candidate_profile=candidate.to_embedding_text(),
            job_requirements=job_requirements.to_embedding_text(),
        )

        for attempt in range(self.max_retries + 1):
            try:
                import ollama

                logger.debug(
                    "LLM evaluating │ candidate={} │ attempt={}",
                    candidate.id,
                    attempt + 1,
                )

                response = ollama.chat(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    options={
                        "temperature": 0.1,
                        "num_predict": 1024,
                    },
                )

                content = response["message"]["content"]
                parsed = extract_json_from_llm_response(content)

                if parsed:
                    evaluation = LLMEvaluation(
                        technical_skill_match=self._safe_float(parsed.get("technical_skill_match", 0), 10),
                        relevant_experience=self._safe_float(parsed.get("relevant_experience", 0), 10),
                        project_relevance=self._safe_float(parsed.get("project_relevance", 0), 10),
                        education_fit=self._safe_float(parsed.get("education_fit", 0), 10),
                        career_growth=self._safe_float(parsed.get("career_growth", 0), 10),
                        communication=self._safe_float(parsed.get("communication", 0), 10),
                        leadership=self._safe_float(parsed.get("leadership", 0), 10),
                        overall_fit=self._safe_float(parsed.get("overall_fit", 0), 10),
                        reasoning=str(parsed.get("reasoning", "")),
                    )
                    logger.info(
                        "LLM evaluated │ candidate={} │ score={:.1f}/100",
                        candidate.id,
                        evaluation.normalized_score,
                    )
                    return evaluation

            except Exception as e:
                logger.warning(
                    "LLM evaluation failed │ candidate={} │ attempt={} │ error={}",
                    candidate.id,
                    attempt + 1,
                    e,
                )

        logger.error("LLM evaluation exhausted retries for {}", candidate.id)
        return LLMEvaluation(reasoning="LLM evaluation failed after retries")

    def evaluate_batch(
        self,
        candidates: List[CandidateProfile],
        job_requirements: JobRequirements,
    ) -> Dict[str, LLMEvaluation]:
        """Evaluate multiple candidates.

        Args:
            candidates: List of candidates to evaluate.
            job_requirements: Job requirements.

        Returns:
            Dict mapping candidate_id → LLMEvaluation.
        """
        logger.info("LLM batch evaluation │ candidates={}", len(candidates))
        results: Dict[str, LLMEvaluation] = {}

        # Limit concurrency to avoid overloading the local Ollama instance
        max_workers = min(3, len(candidates))
        if max_workers == 0:
            return results

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_candidate = {
                executor.submit(self.evaluate_candidate, candidate, job_requirements): candidate
                for candidate in candidates
            }

            for future in as_completed(future_to_candidate):
                candidate = future_to_candidate[future]
                try:
                    evaluation = future.result()
                    results[candidate.id] = evaluation
                except Exception as e:
                    logger.error("LLM evaluation failed for candidate {} │ error={}", candidate.id, e)
                    results[candidate.id] = LLMEvaluation(reasoning="LLM evaluation failed")

        return results

    # ── Helpers ────────────────────────────────────────────────────



    @staticmethod
    def _safe_float(value, max_val: float = 10.0) -> float:
        """Safely convert a value to float within bounds."""
        try:
            f = float(value)
            return max(0.0, min(f, max_val))
        except (ValueError, TypeError):
            return 0.0
