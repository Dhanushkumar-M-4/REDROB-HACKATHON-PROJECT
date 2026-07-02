"""Text utility functions for cleaning, normalization, and extraction."""

import re
from typing import List, Set


def clean_text(text: str) -> str:
    """Clean and normalize text for processing.

    - Strips leading/trailing whitespace
    - Collapses multiple whitespace to single spaces
    - Removes control characters
    """
    if not text:
        return ""
    # Remove control characters (except newlines)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse multiple whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_skill(skill: str) -> str:
    """Normalize a skill name for comparison.

    - Lowercase
    - Strip whitespace
    - Handle common abbreviations
    """
    skill = skill.lower().strip()

    # Common normalizations
    normalizations = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "ml": "machine learning",
        "dl": "deep learning",
        "ai": "artificial intelligence",
        "k8s": "kubernetes",
        "tf": "tensorflow",
        "cv": "computer vision",
        "nlp": "natural language processing",
        "postgres": "postgresql",
        "mongo": "mongodb",
    }

    return normalizations.get(skill, skill)


def extract_skills_from_text(text: str, known_skills: Set[str] = None) -> List[str]:
    """Extract skill names from free-form text.

    Args:
        text: Input text to search for skills.
        known_skills: Optional set of known skill names to match against.

    Returns:
        List of extracted skill names.
    """
    if known_skills is None:
        known_skills = {
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "ruby", "php", "scala", "kotlin", "swift", "r", "matlab",
            "react", "angular", "vue", "svelte", "next.js", "nuxt.js",
            "node.js", "express", "django", "flask", "fastapi", "spring",
            "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "scipy",
            "machine learning", "deep learning", "nlp", "computer vision",
            "reinforcement learning", "generative ai", "llm",
            "git", "ci/cd", "devops", "agile", "scrum", "jira",
            "html", "css", "rest", "graphql", "grpc", "microservices",
            "spark", "hadoop", "kafka", "airflow", "mlops", "data engineering",
            "linux", "bash", "powershell",
        }

    text_lower = text.lower()
    found = []

    for skill in sorted(known_skills):
        # Use word boundary matching for short skills
        if len(skill) <= 3:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found.append(skill)
        else:
            if skill in text_lower:
                found.append(skill)

    return sorted(set(found))


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to max_length, appending suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences (simple heuristic)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def extract_json_from_llm_response(content: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown code blocks and partial texts.

    Args:
        content: The raw text response from the LLM.

    Returns:
        The parsed JSON dictionary, or None if parsing fails.
    """
    import json

    # Try direct JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in text
    brace_match = re.search(r"\{.*\}", content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None

