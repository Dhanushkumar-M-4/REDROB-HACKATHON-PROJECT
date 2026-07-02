"""FastAPI routes for the candidate ranking system."""

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel

from app.models.ranking import RankingResult

router = APIRouter()


def _get_pipeline():
    """Lazy import to break circular dependency with app.main."""
    from app.main import get_pipeline
    return get_pipeline()


# ── Request / Response Models ─────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    candidates_loaded: int = 0
    faiss_index_size: int = 0
    ollama_available: bool = False


class RankRequest(BaseModel):
    """Request body for ranking with inline JD text."""
    job_description: str


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check system health and component status."""
    pipeline = _get_pipeline()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        candidates_loaded=len(pipeline.candidates),
        faiss_index_size=pipeline.vector_store.size if pipeline.vector_store else 0,
        ollama_available=pipeline.llm_ranker.is_available,
    )


@router.post("/rank", response_model=RankingResult, tags=["Ranking"])
async def rank_candidates(
    job_description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Rank candidates against a job description.

    Accepts either:
    - A `job_description` form field with raw text
    - A `file` upload (TXT, PDF, DOCX)

    Returns ranked candidates with hybrid scores.
    """
    pipeline = _get_pipeline()

    # Get JD text from form or file
    jd_text = None

    if file is not None:
        logger.info("Received JD file upload │ filename={}", file.filename)
        try:
            content = await file.read()
            if file.filename and file.filename.endswith((".pdf", ".docx")):
                # Save temporarily for parsing
                import tempfile
                from pathlib import Path

                suffix = Path(file.filename).suffix
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                from app.parsing.file_loader import FileLoader
                jd_text = FileLoader.load(tmp_path)

                # Cleanup
                Path(tmp_path).unlink(missing_ok=True)
            else:
                jd_text = content.decode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read uploaded file: {e}",
            )

    elif job_description is not None:
        jd_text = job_description

    if not jd_text or not jd_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No job description provided. Send 'job_description' form field or upload a file.",
        )

    # Ensure candidates are loaded
    if not pipeline.candidates:
        try:
            logger.info("Loading candidates for ranking...")
            pipeline.run(
                jd_source=jd_text,
                export_csv=True,
                export_json=True,
                display_table=False,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline execution failed: {e}",
            )
    else:
        try:
            result = pipeline.rank_with_jd_text(
                jd_text=jd_text,
                export_csv=True,
                display_table=False,
            )
            return result
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ranking failed: {e}",
            )

    if pipeline.latest_result:
        return pipeline.latest_result

    raise HTTPException(status_code=500, detail="No ranking results available")


@router.get("/candidate/{candidate_id}", tags=["Candidates"])
async def get_candidate(candidate_id: str):
    """Get a specific candidate's profile and ranking information.

    Args:
        candidate_id: The unique candidate identifier.

    Returns:
        Candidate profile with ranking scores.
    """
    pipeline = _get_pipeline()

    result = pipeline.get_candidate(candidate_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate not found: {candidate_id}",
        )

    return result
