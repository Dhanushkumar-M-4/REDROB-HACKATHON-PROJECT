"""Candidate data models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """Structured representation of a candidate's profile."""

    id: str = Field(..., description="Unique candidate identifier")
    name: str = Field(..., description="Full name of the candidate")
    experience_years: float = Field(
        default=0.0, ge=0, description="Total years of professional experience"
    )
    skills: List[str] = Field(default_factory=list, description="Technical and soft skills")
    projects: List[str] = Field(
        default_factory=list, description="Notable projects or contributions"
    )
    education: str = Field(default="", description="Highest education qualification")
    certifications: List[str] = Field(
        default_factory=list, description="Professional certifications"
    )
    achievements: List[str] = Field(
        default_factory=list, description="Key achievements and awards"
    )
    summary: str = Field(default="", description="Professional summary or bio")
    raw_text: str = Field(
        default="", description="Full raw text for embedding generation", repr=False
    )

    def to_embedding_text(self) -> str:
        """Generate a rich text representation for embedding.

        Combines all profile fields into a single text block
        optimized for semantic encoding.
        """
        parts = [
            f"Candidate: {self.name}",
            f"Experience: {self.experience_years} years",
            f"Skills: {', '.join(self.skills)}" if self.skills else "",
            f"Education: {self.education}" if self.education else "",
            f"Projects: {'; '.join(self.projects)}" if self.projects else "",
            f"Certifications: {', '.join(self.certifications)}" if self.certifications else "",
            f"Achievements: {', '.join(self.achievements)}" if self.achievements else "",
            f"Summary: {self.summary}" if self.summary else "",
        ]
        return "\n".join(p for p in parts if p)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "CAND-001",
                "name": "Jane Doe",
                "experience_years": 5.0,
                "skills": ["Python", "Machine Learning", "TensorFlow"],
                "projects": ["Built recommendation engine serving 1M users"],
                "education": "M.S. Computer Science, Stanford University",
                "certifications": ["AWS ML Specialty"],
                "achievements": ["Led team of 8 engineers"],
                "summary": "Senior ML Engineer with 5 years of experience.",
            }
        }


class CandidateCollection(BaseModel):
    """A collection of parsed candidate profiles."""

    candidates: List[CandidateProfile] = Field(default_factory=list)
    source_file: Optional[str] = None
    total_count: int = 0

    def model_post_init(self, __context) -> None:
        """Update total_count after initialization."""
        self.total_count = len(self.candidates)
