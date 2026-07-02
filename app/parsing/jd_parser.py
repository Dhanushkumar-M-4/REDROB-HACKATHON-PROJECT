"""Job description parser — extracts structured requirements using LLM or fallback regex."""

import json
import re
from pathlib import Path
from typing import Optional, Union

from loguru import logger

from app.models.job import JobDescription, JobRequirements
from app.parsing.file_loader import FileLoader
from app.prompts.templates import PromptTemplates
from app.utils.text_utils import extract_json_from_llm_response


class JDParser:
    """Parses job descriptions into structured JobRequirements.

    Primary: Uses Ollama LLM for intelligent extraction.
    Fallback: Uses regex/keyword-based extraction when LLM is unavailable.
    """

    def __init__(self, ollama_model: str = "llama3", ollama_timeout: int = 120):
        self.ollama_model = ollama_model
        self.ollama_timeout = ollama_timeout

    def parse(self, source: Union[str, Path]) -> JobDescription:
        """Parse a job description from file path or raw text.

        Args:
            source: File path or raw JD text.

        Returns:
            JobDescription with extracted requirements.
        """
        path = Path(source)
        if path.exists() and path.is_file():
            raw_text = FileLoader.load(path)
            if not isinstance(raw_text, str):
                raise ValueError(f"Expected text from JD file, got {type(raw_text)}")
            source_file = str(path)
        else:
            raw_text = str(source)
            source_file = None

        logger.info("Parsing job description │ length={} chars", len(raw_text))

        # Try LLM extraction first, fall back to regex
        requirements = self._extract_with_llm(raw_text)
        if requirements is None:
            logger.warning("LLM extraction failed, using fallback regex parser")
            requirements = self._extract_with_regex(raw_text)

        requirements.raw_text = raw_text

        return JobDescription(
            source_file=source_file,
            raw_text=raw_text,
            requirements=requirements,
        )

    def _extract_with_llm(self, text: str) -> Optional[JobRequirements]:
        """Extract requirements using Ollama LLM."""
        try:
            import ollama

            prompt = PromptTemplates.requirement_extraction(text)
            logger.info("Sending JD to LLM for requirement extraction │ model={}", self.ollama_model)

            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 2048},
            )

            content = response["message"]["content"]
            parsed = extract_json_from_llm_response(content)

            if parsed:
                requirements = JobRequirements(
                    role=parsed.get("role", ""),
                    required_skills=self._ensure_list(parsed.get("required_skills", [])),
                    preferred_skills=self._ensure_list(parsed.get("preferred_skills", [])),
                    experience_min=float(parsed.get("experience_min", 0)),
                    experience_max=float(parsed.get("experience_max", 99)),
                    education=parsed.get("education", ""),
                    soft_skills=self._ensure_list(parsed.get("soft_skills", [])),
                    responsibilities=self._ensure_list(parsed.get("responsibilities", [])),
                )
                logger.info("LLM extracted │ role={} │ skills={}", requirements.role, len(requirements.required_skills))
                return requirements

        except ImportError:
            logger.warning("Ollama package not installed")
        except Exception as e:
            logger.warning("LLM extraction error: {}", e)

        return None

    def _extract_with_regex(self, text: str) -> JobRequirements:
        """Fallback: extract requirements using regex patterns."""
        logger.info("Using regex fallback for JD parsing")

        return JobRequirements(
            role=self._extract_role(text),
            required_skills=self._extract_skills_section(text, "required"),
            preferred_skills=self._extract_skills_section(text, "preferred"),
            experience_min=self._extract_experience_min(text),
            experience_max=self._extract_experience_max(text),
            education=self._extract_education(text),
            soft_skills=self._extract_soft_skills(text),
            responsibilities=self._extract_responsibilities(text),
        )



    # ── Regex Extraction Helpers ──────────────────────────────────

    @staticmethod
    def _extract_role(text: str) -> str:
        """Extract job title from text."""
        patterns = [
            r"(?:job\s*title|position|role)\s*:?\s*(.+?)(?:\n|$)",
            r"^(.+?(?:engineer|developer|scientist|analyst|manager|architect|designer|lead))\s*$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()[:100]

        # Use first non-empty line as fallback
        for line in text.split("\n"):
            if line.strip() and len(line.strip()) < 100:
                return line.strip()
        return "Unknown Role"

    @staticmethod
    def _extract_skills_section(text: str, skill_type: str = "required") -> list:
        """Extract skills from a specific section."""
        common_tech = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
            "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "Git", "CI/CD", "DevOps", "REST", "GraphQL", "Microservices",
            "Spark", "Hadoop", "Kafka", "Airflow", "MLOps",
            "Linux", "Terraform", "Jenkins", "Data Engineering",
        ]
        text_lower = text.lower()
        found = [s for s in common_tech if s.lower() in text_lower]
        return found

    @staticmethod
    def _extract_experience_min(text: str) -> float:
        """Extract minimum experience requirement."""
        patterns = [
            r"(\d+)\s*\+?\s*years?\s*(?:of\s*)?experience",
            r"minimum\s*(?:of\s*)?(\d+)\s*years?",
            r"at\s*least\s*(\d+)\s*years?",
            r"(\d+)\s*-\s*\d+\s*years?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0

    @staticmethod
    def _extract_experience_max(text: str) -> float:
        """Extract maximum experience preference."""
        match = re.search(r"\d+\s*-\s*(\d+)\s*years?", text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 99.0

    @staticmethod
    def _extract_education(text: str) -> str:
        """Extract education requirement."""
        patterns = [
            r"((?:Ph\.?D|Doctorate|Master'?s?|M\.S\.?|M\.B\.A\.?|Bachelor'?s?|B\.S\.?)\s*(?:in\s+[\w\s,]+)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:150]
        return ""

    @staticmethod
    def _extract_soft_skills(text: str) -> list:
        """Extract soft skills from text."""
        soft_skills_list = [
            "Leadership", "Communication", "Teamwork", "Problem Solving",
            "Critical Thinking", "Adaptability", "Collaboration",
            "Time Management", "Mentoring", "Presentation",
        ]
        text_lower = text.lower()
        return [s for s in soft_skills_list if s.lower() in text_lower]

    @staticmethod
    def _extract_responsibilities(text: str) -> list:
        """Extract responsibilities from bullet points or numbered lists."""
        responsibilities = []
        # Look for bullet points or numbered items
        bullet_patterns = re.findall(
            r"(?:^|\n)\s*(?:[-•*▪]|\d+[.)]\s)\s*(.+?)(?=\n|$)",
            text,
        )
        for item in bullet_patterns[:10]:
            clean = item.strip()
            if len(clean) > 15:
                responsibilities.append(clean)

        return responsibilities

    @staticmethod
    def _ensure_list(value) -> list:
        """Ensure a value is a list of strings."""
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return []
