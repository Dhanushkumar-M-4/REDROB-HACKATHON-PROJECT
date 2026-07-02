"""Unified file loader supporting CSV, JSON, TXT, PDF, and DOCX formats."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from loguru import logger


class FileLoader:
    """Loads candidate data and job descriptions from various file formats.

    Supported formats:
        - CSV  → pandas DataFrame
        - JSON → list of dicts or dict
        - TXT  → raw string
        - PDF  → extracted text (via PyMuPDF)
        - DOCX → extracted text (via python-docx)
    """

    @staticmethod
    def load(file_path: Union[str, Path]) -> Any:
        """Auto-detect file type and load contents.

        Args:
            file_path: Path to the file to load.

        Returns:
            Loaded data (DataFrame, dict, list, or str depending on format).

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file extension is not supported.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        logger.info("Loading file │ path={} │ format={}", path.name, ext)

        loaders = {
            ".csv": FileLoader._load_csv,
            ".json": FileLoader._load_json,
            ".txt": FileLoader._load_txt,
            ".pdf": FileLoader._load_pdf,
            ".docx": FileLoader._load_docx,
        }

        loader = loaders.get(ext)
        if loader is None:
            raise ValueError(
                f"Unsupported file format: {ext}. "
                f"Supported: {', '.join(loaders.keys())}"
            )

        return loader(path)

    @staticmethod
    def load_directory(
        dir_path: Union[str, Path],
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Load all supported files from a directory.

        Args:
            dir_path: Directory containing files to load.
            extensions: Optional filter for specific extensions.

        Returns:
            Dict mapping filename to loaded content.
        """
        directory = Path(dir_path)
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        if extensions is None:
            extensions = [".csv", ".json", ".txt", ".pdf", ".docx"]

        results: Dict[str, Any] = {}
        for file_path in sorted(directory.iterdir()):
            if file_path.suffix.lower() in extensions and file_path.is_file():
                try:
                    results[file_path.name] = FileLoader.load(file_path)
                    logger.debug("Loaded: {}", file_path.name)
                except Exception as e:
                    logger.warning("Failed to load {} │ error={}", file_path.name, e)

        logger.info("Loaded {} files from {}", len(results), directory.name)
        return results

    # ── Private Loaders ────────────────────────────────────────────

    @staticmethod
    def _load_csv(path: Path) -> pd.DataFrame:
        """Load a CSV file into a pandas DataFrame."""
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1")

        logger.debug("CSV loaded │ rows={} │ columns={}", len(df), list(df.columns))
        return df

    @staticmethod
    def _load_json(path: Path) -> Union[List[Dict], Dict]:
        """Load a JSON file."""
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = len(data) if isinstance(data, list) else 1
        logger.debug("JSON loaded │ items={}", count)
        return data

    @staticmethod
    def _load_txt(path: Path) -> str:
        """Load a plain text file."""
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")

        logger.debug("TXT loaded │ chars={}", len(text))
        return text

    @staticmethod
    def _load_pdf(path: Path) -> str:
        """Extract text from a PDF using PyMuPDF (fitz)."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF parsing. Install with: pip install PyMuPDF"
            )

        text_parts = []
        try:
            doc = fitz.open(str(path))
            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(page_text)
            doc.close()
        except Exception as e:
            raise RuntimeError(f"PDF parsing failed for {path.name}: {e}")

        full_text = "\n\n".join(text_parts)
        logger.debug("PDF loaded │ pages={} │ chars={}", len(text_parts), len(full_text))
        return full_text

    @staticmethod
    def _load_docx(path: Path) -> str:
        """Extract text from a DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX parsing. Install with: pip install python-docx"
            )

        try:
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        except Exception as e:
            raise RuntimeError(f"DOCX parsing failed for {path.name}: {e}")

        full_text = "\n".join(paragraphs)
        logger.debug("DOCX loaded │ paragraphs={} │ chars={}", len(paragraphs), len(full_text))
        return full_text
