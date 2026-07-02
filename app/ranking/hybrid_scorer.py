"""Hybrid scorer — combines semantic, LLM, experience, skill, and education scores."""

from typing import Dict, List

from loguru import logger

from app.models.candidate import CandidateProfile
from app.models.job import JobRequirements
from app.models.ranking import LLMEvaluation, RankedCandidate


class HybridScorer:
    """Computes hybrid ranking scores from multiple signal sources.

    Weights:
        - 40% Semantic Similarity
        - 30% LLM Score
        - 15% Experience Score
        - 10% Skill Coverage
        - 5%  Education
    """

    def __init__(
        self,
        weight_semantic: float = 0.40,
        weight_llm: float = 0.30,
        weight_experience: float = 0.15,
        weight_skills: float = 0.10,
        weight_education: float = 0.05,
    ):
        self.weight_semantic = weight_semantic
        self.weight_llm = weight_llm
        self.weight_experience = weight_experience
        self.weight_skills = weight_skills
        self.weight_education = weight_education

        # Verify weights sum to ~1.0
        total = (
            weight_semantic + weight_llm + weight_experience
            + weight_skills + weight_education
        )
        if abs(total - 1.0) > 0.01:
            logger.warning("Hybrid weights sum to {:.3f}, expected 1.0", total)

    def compute_scores(
        self,
        candidates: List[CandidateProfile],
        job_requirements: JobRequirements,
        semantic_scores: Dict[str, float],
        llm_evaluations: Dict[str, LLMEvaluation],
    ) -> List[RankedCandidate]:
        """Compute hybrid scores and produce ranked candidates.

        Args:
            candidates: List of candidate profiles.
            job_requirements: Structured job requirements.
            semantic_scores: Dict of candidate_id → semantic score (0-100).
            llm_evaluations: Dict of candidate_id → LLMEvaluation.

        Returns:
            List of RankedCandidate sorted by final_score descending.
        """
        logger.info("Computing hybrid scores for {} candidates", len(candidates))

        candidate_map = {c.id: c for c in candidates}
        jd_skills = job_requirements.get_all_skills()
        ranked: List[RankedCandidate] = []

        for candidate in candidates:
            cid = candidate.id

            # ── Semantic Score (0-100) ─────────────────────────────
            sem_score = semantic_scores.get(cid, 0.0)

            # ── LLM Score (0-100) ──────────────────────────────────
            llm_eval = llm_evaluations.get(cid, LLMEvaluation())
            llm_score = llm_eval.normalized_score

            # ── Experience Score (0-100) ───────────────────────────
            exp_score = self._compute_experience_score(
                candidate.experience_years,
                job_requirements.experience_min,
                job_requirements.experience_max,
            )

            # ── Skill Coverage Score (0-100) ───────────────────────
            skill_score = self._compute_skill_score(
                candidate.skills, jd_skills
            )

            # ── Education Score (0-100) ────────────────────────────
            edu_score = self._compute_education_score(
                candidate.education, job_requirements.education
            )

            # ── Final Weighted Score ───────────────────────────────
            final_score = (
                self.weight_semantic * sem_score
                + self.weight_llm * llm_score
                + self.weight_experience * exp_score
                + self.weight_skills * skill_score
                + self.weight_education * edu_score
            )

            # Clamp to 0-100
            final_score = max(0.0, min(100.0, round(final_score, 2)))

            ranked_candidate = RankedCandidate(
                rank=0,  # Will be set after sorting
                candidate_id=cid,
                candidate_name=candidate.name,
                semantic_score=round(sem_score, 2),
                llm_score=round(llm_score, 2),
                experience_score=round(exp_score, 2),
                skill_score=round(skill_score, 2),
                education_score=round(edu_score, 2),
                final_score=final_score,
                reason=llm_eval.reasoning or self._generate_default_reason(
                    candidate, sem_score, exp_score, skill_score
                ),
                llm_evaluation=llm_eval,
            )
            ranked.append(ranked_candidate)

        # Sort by final_score descending
        ranked.sort(key=lambda r: r.final_score, reverse=True)

        # Assign ranks
        for i, rc in enumerate(ranked, start=1):
            rc.rank = i

        logger.info(
            "Hybrid scoring complete │ top={} ({:.2f}) │ bottom={} ({:.2f})",
            ranked[0].candidate_name if ranked else "N/A",
            ranked[0].final_score if ranked else 0,
            ranked[-1].candidate_name if ranked else "N/A",
            ranked[-1].final_score if ranked else 0,
        )

        return ranked

    # ── Score Computation Methods ─────────────────────────────────

    @staticmethod
    def _compute_experience_score(
        candidate_years: float,
        required_min: float,
        required_max: float,
    ) -> float:
        """Score experience fit on a 0-100 scale.

        Perfect score if within [min, max] range.
        Partial credit for close matches.
        """
        if required_min == 0 and required_max >= 99:
            # No specific requirement — give moderate score based on experience
            return min(candidate_years * 10, 100)

        if required_min <= candidate_years <= required_max:
            # Within range — perfect score
            return 100.0

        if candidate_years < required_min:
            # Under-experienced
            if required_min == 0:
                return 50.0
            ratio = candidate_years / required_min
            return max(0, ratio * 80)  # Up to 80 for close matches

        # Over-experienced
        overshoot = candidate_years - required_max
        penalty = min(overshoot * 5, 40)  # -5 per extra year, max -40
        return max(60, 100 - penalty)

    @staticmethod
    def _compute_skill_score(
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> float:
        """Score skill coverage on a 0-100 scale.

        Based on the ratio of required skills that the candidate possesses.
        """
        if not required_skills:
            return 70.0 if candidate_skills else 50.0

        candidate_lower = {s.lower().strip() for s in candidate_skills}
        required_lower = {s.lower().strip() for s in required_skills}

        if not required_lower:
            return 70.0

        # Count matches (including partial matches)
        matches = 0
        for req_skill in required_lower:
            if req_skill in candidate_lower:
                matches += 1
            else:
                # Check partial matches (e.g., "machine learning" matches "ml")
                for cand_skill in candidate_lower:
                    if req_skill in cand_skill or cand_skill in req_skill:
                        matches += 0.5
                        break

        coverage = matches / len(required_lower)
        return min(100.0, coverage * 100)

    @staticmethod
    def _compute_education_score(
        candidate_education: str,
        required_education: str,
    ) -> float:
        """Score education fit on a 0-100 scale."""
        if not required_education:
            return 70.0  # No specific requirement

        edu_levels = {
            "phd": 100, "doctorate": 100, "ph.d": 100,
            "master": 85, "m.s": 85, "m.s.": 85, "mba": 85, "m.b.a": 85,
            "bachelor": 70, "b.s": 70, "b.s.": 70, "b.tech": 70,
            "associate": 50,
            "diploma": 40,
            "high school": 30,
        }

        def get_level(text: str) -> int:
            text_lower = text.lower()
            for keyword, score in edu_levels.items():
                if keyword in text_lower:
                    return score
            return 50  # Default

        candidate_level = get_level(candidate_education)
        required_level = get_level(required_education)

        if candidate_level >= required_level:
            return 100.0
        else:
            ratio = candidate_level / max(required_level, 1)
            return max(30.0, ratio * 100)

    @staticmethod
    def _generate_default_reason(
        candidate: CandidateProfile,
        semantic_score: float,
        experience_score: float,
        skill_score: float,
    ) -> str:
        """Generate a default reason when LLM is unavailable."""
        parts = []
        if semantic_score >= 70:
            parts.append("Strong semantic match to job requirements")
        elif semantic_score >= 50:
            parts.append("Moderate semantic alignment with the role")
        else:
            parts.append("Limited semantic match to job requirements")

        if experience_score >= 80:
            parts.append(f"with {candidate.experience_years} years of relevant experience")
        elif experience_score >= 50:
            parts.append(f"with {candidate.experience_years} years of experience")

        if skill_score >= 70:
            parts.append(f"and strong skill coverage ({len(candidate.skills)} matching skills)")

        return ". ".join(parts) + "." if parts else "Evaluated based on available profile data."
