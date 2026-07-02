"""Job description data models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    """Structured representation of job description requirements."""

    role: str = Field(default="", description="Job title / role name")
    required_skills: List[str] = Field(
        default_factory=list, description="Must-have technical skills"
    )
    preferred_skills: List[str] = Field(
        default_factory=list, description="Nice-to-have skills"
    )
    experience_min: float = Field(
        default=0.0, ge=0, description="Minimum years of experience required"
    )
    experience_max: float = Field(
        default=99.0, ge=0, description="Maximum years of experience preferred"
    )
    education: str = Field(
        default="", description="Required education level"
    )
    soft_skills: List[str] = Field(
        default_factory=list, description="Required soft skills"
    )
    responsibilities: List[str] = Field(
        default_factory=list, description="Key job responsibilities"
    )
    raw_text: str = Field(
        default="", description="Original job description text", repr=False
    )

    def to_embedding_text(self) -> str:
        """Generate a rich text representation for embedding.

        Combines all requirement fields into a single text block
        optimized for semantic encoding.
        """
        parts = [
            f"Role: {self.role}" if self.role else "",
            f"Required Skills: {', '.join(self.required_skills)}" if self.required_skills else "",
            f"Preferred Skills: {', '.join(self.preferred_skills)}" if self.preferred_skills else "",
            f"Experience: {self.experience_min}-{self.experience_max} years",
            f"Education: {self.education}" if self.education else "",
            f"Soft Skills: {', '.join(self.soft_skills)}" if self.soft_skills else "",
            f"Responsibilities: {'; '.join(self.responsibilities)}" if self.responsibilities else "",
        ]
        return "\n".join(p for p in parts if p)

    def get_all_skills(self) -> List[str]:
        """Return combined list of all required and preferred skills (lowercase)."""
        return [s.lower().strip() for s in self.required_skills + self.preferred_skills]

    class Config:
        json_schema_extra = {
            "example": {
                "role": "Senior Machine Learning Engineer",
                "required_skills": ["Python", "TensorFlow", "PyTorch", "MLOps"],
                "preferred_skills": ["Kubernetes", "Spark"],
                "experience_min": 5.0,
                "experience_max": 10.0,
                "education": "M.S. or Ph.D. in Computer Science",
                "soft_skills": ["Leadership", "Communication"],
                "responsibilities": [
                    "Design and deploy ML models at scale",
                    "Lead a team of 5 engineers",
                ],
            }
        }


class JobDescription(BaseModel):
    """Wrapper for a complete job description document."""

    source_file: Optional[str] = None
    raw_text: str = Field(default="", description="Full job description text")
    requirements: Optional[JobRequirements] = None
