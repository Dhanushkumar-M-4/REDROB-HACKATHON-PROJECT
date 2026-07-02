"""Prompt templates for LLM interactions throughout the pipeline."""


class PromptTemplates:
    """Centralized prompt templates for all LLM-powered pipeline stages.

    Each method returns a fully-formatted prompt string ready to send to the LLM.
    All prompts instruct the model to return structured JSON output.
    """

    @staticmethod
    def requirement_extraction(job_description: str) -> str:
        """Generate a prompt to extract structured requirements from a JD.

        Args:
            job_description: Raw job description text.

        Returns:
            Formatted prompt string.
        """
        return f"""You are an expert HR analyst. Extract structured requirements from the following job description.

Return ONLY a valid JSON object with these exact keys:
{{
    "role": "Job title",
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill1", "skill2"],
    "experience_min": 0,
    "experience_max": 99,
    "education": "Required education level",
    "soft_skills": ["skill1", "skill2"],
    "responsibilities": ["responsibility1", "responsibility2"]
}}

Rules:
- required_skills: Must-have technical skills explicitly stated
- preferred_skills: Nice-to-have or bonus skills
- experience_min/max: Numeric years (use 0 and 99 if not specified)
- Be precise and extract only what's mentioned
- Return ONLY the JSON, no explanation

JOB DESCRIPTION:
{job_description}"""

    @staticmethod
    def candidate_evaluation(
        candidate_profile: str,
        job_requirements: str,
    ) -> str:
        """Generate a prompt to evaluate a candidate against job requirements.

        Args:
            candidate_profile: Candidate's profile text.
            job_requirements: Structured job requirements text.

        Returns:
            Formatted prompt string.
        """
        return f"""You are a senior technical recruiter. Evaluate this candidate against the job requirements.

Score each dimension from 0-10 (0=no match, 10=perfect match).

Return ONLY a valid JSON object with these exact keys:
{{
    "technical_skill_match": 0,
    "relevant_experience": 0,
    "project_relevance": 0,
    "education_fit": 0,
    "career_growth": 0,
    "communication": 0,
    "leadership": 0,
    "overall_fit": 0,
    "reasoning": "Punchy 2-bullet summary (Top Strength, Main Gap)"
}}

Scoring Guidelines:
- technical_skill_match: How well do the candidate's skills match required/preferred skills?
- relevant_experience: Is their experience duration and domain relevant?
- project_relevance: Are their projects aligned with the role's responsibilities?
- education_fit: Does their education meet or exceed requirements?
- career_growth: Does their career trajectory show progression toward this role?
- communication: Evidence of communication skills (presentations, publications, mentoring)?
- leadership: Evidence of leadership (team lead, mentoring, initiative)?
- overall_fit: Holistic assessment of candidate-role alignment

Return ONLY the JSON, no explanation outside the JSON.

JOB REQUIREMENTS:
{job_requirements}

CANDIDATE PROFILE:
{candidate_profile}"""

    @staticmethod
    def candidate_comparison(
        candidate_a: str,
        candidate_b: str,
        job_requirements: str,
    ) -> str:
        """Generate a prompt to compare two candidates head-to-head.

        Args:
            candidate_a: First candidate's profile text.
            candidate_b: Second candidate's profile text.
            job_requirements: Structured job requirements text.

        Returns:
            Formatted prompt string.
        """
        return f"""You are a senior technical recruiter. Compare these two candidates for the given role.

Return ONLY a valid JSON object:
{{
    "preferred_candidate": "A" or "B",
    "confidence": 0.0 to 1.0,
    "comparison": {{
        "technical_skills": "A" or "B" or "Tie",
        "experience": "A" or "B" or "Tie",
        "education": "A" or "B" or "Tie",
        "project_relevance": "A" or "B" or "Tie",
        "overall_fit": "A" or "B" or "Tie"
    }},
    "reasoning": "Brief explanation of why the preferred candidate is better suited"
}}

Return ONLY the JSON.

JOB REQUIREMENTS:
{job_requirements}

CANDIDATE A:
{candidate_a}

CANDIDATE B:
{candidate_b}"""

    @staticmethod
    def final_ranking_explanation(
        candidate_name: str,
        rank: int,
        scores: dict,
        job_role: str,
    ) -> str:
        """Generate a prompt for a human-readable ranking explanation.

        Args:
            candidate_name: Name of the candidate.
            rank: Final rank position.
            scores: Dictionary of all score components.
            job_role: The job role title.

        Returns:
            Formatted prompt string.
        """
        scores_text = "\n".join(f"  - {k}: {v:.1f}/100" for k, v in scores.items())

        return f"""You are a senior recruiter writing a brief ranking explanation.

Write a 2-3 sentence explanation for why this candidate is ranked #{rank} for the {job_role} role.
Be specific about their strengths and any gaps.

Candidate: {candidate_name}
Rank: #{rank}
Scores:
{scores_text}

Return ONLY a concise 2-3 sentence explanation. No JSON, no bullet points, just plain text."""
