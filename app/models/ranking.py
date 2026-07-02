"""Ranking result data models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class LLMEvaluation(BaseModel):
    """LLM-generated evaluation scores for a candidate."""

    technical_skill_match: float = Field(default=0.0, ge=0, le=10, description="Technical skills alignment (0-10)")
    relevant_experience: float = Field(default=0.0, ge=0, le=10, description="Relevance of experience (0-10)")
    project_relevance: float = Field(default=0.0, ge=0, le=10, description="Project relevance (0-10)")
    education_fit: float = Field(default=0.0, ge=0, le=10, description="Education alignment (0-10)")
    career_growth: float = Field(default=0.0, ge=0, le=10, description="Career trajectory (0-10)")
    communication: float = Field(default=0.0, ge=0, le=10, description="Communication skills (0-10)")
    leadership: float = Field(default=0.0, ge=0, le=10, description="Leadership potential (0-10)")
    overall_fit: float = Field(default=0.0, ge=0, le=10, description="Overall fit for the role (0-10)")
    reasoning: str = Field(default="", description="Brief reasoning for the evaluation")

    @property
    def average_score(self) -> float:
        """Calculate the average of all 8 evaluation dimensions."""
        scores = [
            self.technical_skill_match,
            self.relevant_experience,
            self.project_relevance,
            self.education_fit,
            self.career_growth,
            self.communication,
            self.leadership,
            self.overall_fit,
        ]
        return sum(scores) / len(scores)

    @property
    def normalized_score(self) -> float:
        """Normalize the average score to 0-100 scale."""
        return (self.average_score / 10.0) * 100.0


class RankedCandidate(BaseModel):
    """A candidate with all computed ranking scores."""

    rank: int = Field(default=0, ge=0, description="Final rank position")
    candidate_id: str = Field(..., description="Unique candidate identifier")
    candidate_name: str = Field(..., description="Full name")
    semantic_score: float = Field(default=0.0, ge=0, le=100, description="Semantic similarity score (0-100)")
    llm_score: float = Field(default=0.0, ge=0, le=100, description="LLM evaluation score (0-100)")
    experience_score: float = Field(default=0.0, ge=0, le=100, description="Experience match score (0-100)")
    skill_score: float = Field(default=0.0, ge=0, le=100, description="Skill coverage score (0-100)")
    education_score: float = Field(default=0.0, ge=0, le=100, description="Education match score (0-100)")
    final_score: float = Field(default=0.0, ge=0, le=100, description="Weighted hybrid score (0-100)")
    reason: str = Field(default="", description="LLM-generated ranking explanation")

    # Optional detailed evaluation
    llm_evaluation: Optional[LLMEvaluation] = Field(
        default=None, exclude=True, description="Detailed LLM evaluation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "candidate_id": "CAND-001",
                "candidate_name": "Jane Doe",
                "semantic_score": 92.5,
                "llm_score": 88.0,
                "experience_score": 85.0,
                "skill_score": 90.0,
                "education_score": 95.0,
                "final_score": 90.25,
                "reason": "Strong ML background with relevant project experience.",
            }
        }


class RankingResult(BaseModel):
    """Complete ranking result for an API response."""

    job_role: str = Field(default="", description="The job role being ranked for")
    total_candidates: int = Field(default=0, description="Total candidates evaluated")
    ranked_candidates: List[RankedCandidate] = Field(
        default_factory=list, description="Ordered list of ranked candidates"
    )
    output_file: Optional[str] = Field(
        default=None, description="Path to exported CSV file"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_role": "Senior ML Engineer",
                "total_candidates": 20,
                "ranked_candidates": [],
                "output_file": "data/output/ranked_candidates.csv",
            }
        }
