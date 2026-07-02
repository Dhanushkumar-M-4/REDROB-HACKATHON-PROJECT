"""Candidate data parser — transforms raw data into CandidateProfile objects."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from loguru import logger

from app.models.candidate import CandidateCollection, CandidateProfile
from app.parsing.file_loader import FileLoader


class CandidateParser:
    """Parses candidate data from various sources into structured profiles.

    Supports:
        - CSV files with structured columns
        - JSON files (list of candidate dicts)
        - Raw text / resume files (PDF, DOCX, TXT)
    """

    # ── Column Name Mappings (handles common variations) ───────────
    COLUMN_MAP: Dict[str, List[str]] = {
        "id": ["id", "candidate_id", "candidateid", "cand_id", "ID"],
        "name": ["name", "candidate_name", "full_name", "fullname", "Name"],
        "experience_years": [
            "experience_years", "experience", "years_of_experience",
            "exp_years", "yoe", "Experience (Years)", "experience_yrs",
        ],
        "skills": ["skills", "technical_skills", "skill_set", "skillset", "Skills"],
        "projects": ["projects", "project_experience", "notable_projects", "Projects"],
        "education": ["education", "degree", "qualification", "Education"],
        "certifications": [
            "certifications", "certificates", "certs", "Certifications",
        ],
        "achievements": ["achievements", "awards", "accomplishments", "Achievements"],
        "summary": ["summary", "bio", "about", "profile_summary", "Summary"],
    }

    def parse_file(self, file_path: Union[str, Path]) -> CandidateCollection:
        """Parse a single file into a CandidateCollection.

        Args:
            file_path: Path to the candidate data file.

        Returns:
            CandidateCollection with parsed profiles.
        """
        path = Path(file_path)
        logger.info("Parsing candidate file │ path={}", path.name)

        data = FileLoader.load(path)

        if isinstance(data, pd.DataFrame):
            candidates = self._parse_dataframe(data)
        elif isinstance(data, list):
            candidates = self._parse_dict_list(data)
        elif isinstance(data, str):
            candidates = self._parse_raw_text(data, source_name=path.stem)
        else:
            raise ValueError(f"Unexpected data type from file loader: {type(data)}")

        collection = CandidateCollection(
            candidates=candidates,
            source_file=str(path),
        )
        logger.info(
            "Parsed {} candidates from {}", collection.total_count, path.name
        )
        return collection

    def parse_directory(self, dir_path: Union[str, Path]) -> CandidateCollection:
        """Parse all candidate files in a directory.

        Args:
            dir_path: Directory containing candidate files.

        Returns:
            Combined CandidateCollection from all files.
        """
        directory = Path(dir_path)
        all_candidates: List[CandidateProfile] = []

        files = sorted(directory.iterdir())
        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in (
                ".csv", ".json", ".txt", ".pdf", ".docx"
            ):
                try:
                    collection = self.parse_file(file_path)
                    all_candidates.extend(collection.candidates)
                except Exception as e:
                    logger.error("Failed to parse {} │ error={}", file_path.name, e)

        result = CandidateCollection(
            candidates=all_candidates,
            source_file=str(directory),
        )
        logger.info("Total candidates parsed from directory: {}", result.total_count)
        return result

    # ── Private Parsers ────────────────────────────────────────────

    def _parse_dataframe(self, df: pd.DataFrame) -> List[CandidateProfile]:
        """Parse a pandas DataFrame into CandidateProfile list."""
        # Normalize column names
        col_mapping = self._resolve_columns(df.columns.tolist())
        logger.debug("Column mapping resolved: {}", col_mapping)

        candidates = []
        for idx, row in df.iterrows():
            try:
                candidate = self._row_to_profile(row, col_mapping, idx)
                candidates.append(candidate)
            except Exception as e:
                logger.warning("Skipping row {} │ error={}", idx, e)

        return candidates

    def _parse_dict_list(self, data: List[Dict[str, Any]]) -> List[CandidateProfile]:
        """Parse a list of dictionaries into CandidateProfile list."""
        candidates = []
        for idx, item in enumerate(data):
            try:
                candidate = CandidateProfile(
                    id=str(item.get("id", f"CAND-{idx + 1:03d}")),
                    name=str(item.get("name", f"Candidate {idx + 1}")),
                    experience_years=float(item.get("experience_years", 0)),
                    skills=self._to_list(item.get("skills", [])),
                    projects=self._to_list(item.get("projects", [])),
                    education=str(item.get("education", "")),
                    certifications=self._to_list(item.get("certifications", [])),
                    achievements=self._to_list(item.get("achievements", [])),
                    summary=str(item.get("summary", "")),
                )
                candidate.raw_text = candidate.to_embedding_text()
                candidates.append(candidate)
            except Exception as e:
                logger.warning("Skipping dict item {} │ error={}", idx, e)

        return candidates

    def _parse_raw_text(
        self, text: str, source_name: str = "unknown"
    ) -> List[CandidateProfile]:
        """Parse raw text (from resume PDF/DOCX/TXT) into a single CandidateProfile."""
        name = self._extract_name_from_text(text) or source_name
        experience = self._extract_experience_from_text(text)
        skills = self._extract_skills_from_text(text)
        education = self._extract_education_from_text(text)

        candidate = CandidateProfile(
            id=f"CAND-{source_name.upper().replace(' ', '-')}",
            name=name,
            experience_years=experience,
            skills=skills,
            education=education,
            summary=text[:500].strip(),
            raw_text=text,
        )
        return [candidate]

    def _row_to_profile(
        self,
        row: pd.Series,
        col_mapping: Dict[str, Optional[str]],
        idx: int,
    ) -> CandidateProfile:
        """Convert a DataFrame row to a CandidateProfile."""

        def get_val(field: str, default: Any = "") -> Any:
            col = col_mapping.get(field)
            if col is None:
                return default
            val = row.get(col, default)
            if pd.isna(val):
                return default
            return val

        candidate = CandidateProfile(
            id=str(get_val("id", f"CAND-{idx + 1:03d}")),
            name=str(get_val("name", f"Candidate {idx + 1}")),
            experience_years=float(get_val("experience_years", 0)),
            skills=self._to_list(get_val("skills", [])),
            projects=self._to_list(get_val("projects", [])),
            education=str(get_val("education", "")),
            certifications=self._to_list(get_val("certifications", [])),
            achievements=self._to_list(get_val("achievements", [])),
            summary=str(get_val("summary", "")),
        )
        candidate.raw_text = candidate.to_embedding_text()
        return candidate

    def _resolve_columns(
        self, actual_columns: List[str]
    ) -> Dict[str, Optional[str]]:
        """Map expected fields to actual DataFrame column names."""
        actual_lower = {c.lower().strip(): c for c in actual_columns}
        mapping: Dict[str, Optional[str]] = {}

        for field, aliases in self.COLUMN_MAP.items():
            matched = None
            for alias in aliases:
                if alias.lower() in actual_lower:
                    matched = actual_lower[alias.lower()]
                    break
            mapping[field] = matched

        return mapping

    # ── Text Extraction Helpers ────────────────────────────────────

    @staticmethod
    def _extract_name_from_text(text: str) -> str:
        """Attempt to extract a name from the first lines of text."""
        lines = text.strip().split("\n")
        for line in lines[:5]:
            clean = line.strip()
            if 2 <= len(clean.split()) <= 4 and clean.replace(" ", "").isalpha():
                return clean
        return ""

    @staticmethod
    def _extract_experience_from_text(text: str) -> float:
        """Extract years of experience from text using regex."""
        patterns = [
            r"(\d+\.?\d*)\s*\+?\s*years?\s*(?:of\s*)?experience",
            r"experience\s*:?\s*(\d+\.?\d*)\s*years?",
            r"(\d+\.?\d*)\s*yrs?\s*(?:of\s*)?exp",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0

    @staticmethod
    def _extract_skills_from_text(text: str) -> List[str]:
        """Extract skills from text using common tech keywords."""
        common_skills = {
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
            "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
            "machine learning", "deep learning", "nlp", "computer vision",
            "git", "ci/cd", "devops", "agile", "scrum",
            "html", "css", "rest", "graphql", "microservices",
            "spark", "hadoop", "kafka", "airflow", "mlops",
        }
        text_lower = text.lower()
        found = [skill for skill in common_skills if skill in text_lower]
        return sorted(set(found))

    @staticmethod
    def _extract_education_from_text(text: str) -> str:
        """Extract education level from text."""
        patterns = [
            r"(ph\.?d\.?|doctorate)\s+(?:in\s+)?[\w\s]+",
            r"(m\.?s\.?|master(?:'?s)?)\s+(?:in\s+)?[\w\s]+",
            r"(b\.?s\.?|bachelor(?:'?s)?)\s+(?:in\s+)?[\w\s]+",
            r"(m\.?b\.?a\.?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:100]
        return ""

    @staticmethod
    def _to_list(value: Any) -> List[str]:
        """Convert a value to a list of strings."""
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            if not value.strip():
                return []
            # Handle common delimiters
            for delimiter in [";", "|", ","]:
                if delimiter in value:
                    return [v.strip() for v in value.split(delimiter) if v.strip()]
            return [value.strip()]
        return []
