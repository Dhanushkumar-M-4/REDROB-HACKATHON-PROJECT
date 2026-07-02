#!/usr/bin/env python3
"""AI Smart Candidate Ranking System — Main Entry Point.

Orchestrates the full ranking pipeline:
1. Load and parse job description
2. Load and parse candidate data
3. Generate embeddings and build FAISS index
4. Retrieve top candidates via semantic search
5. LLM re-ranking (if Ollama available)
6. Compute hybrid scores
7. Export ranked_candidates.csv
8. Start FastAPI server

Usage:
    python run.py
    python run.py --no-server
    python run.py --jd path/to/jd.txt --candidates path/to/candidates.csv
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Fix for Windows console emoji encoding
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Smart Candidate Ranking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--jd",
        type=str,
        default=None,
        help="Path to job description file (default: data/job_descriptions/)",
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default=None,
        help="Path to candidate data file or directory (default: data/candidates/)",
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Run ranking only, don't start the FastAPI server",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="FastAPI server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="FastAPI server port (default: 8000)",
    )
    return parser.parse_args()


def print_banner(console: Console) -> None:
    """Print the startup banner."""
    banner = Text()
    banner.append("🤖 AI Smart Candidate Ranking System\n", style="bold cyan")
    banner.append("━" * 45 + "\n", style="bright_blue")
    banner.append("  Semantic Search + LLM Re-ranking\n", style="white")
    banner.append("  Powered by FAISS, Sentence Transformers & Ollama\n", style="dim")
    banner.append("━" * 45, style="bright_blue")

    console.print(Panel(banner, border_style="bright_blue", padding=(1, 2)))
    console.print()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    console = Console()

    print_banner(console)

    # ── Step 1: Setup Logging ──────────────────────────────────────
    from app.core.config import settings
    from app.core.logging import setup_logging

    settings.ensure_directories()
    setup_logging(
        log_level=settings.log_level,
        log_file=str(settings.project_root / settings.log_file),
    )

    from loguru import logger

    logger.info("Starting AI Smart Candidate Ranking System")
    logger.info("Project root: {}", project_root)

    # ── Step 2: Run Ranking Pipeline ───────────────────────────────
    console.print("  [bold yellow]⚡ Initializing ranking pipeline...[/bold yellow]")
    console.print()

    from app.services.pipeline import RankingPipeline

    pipeline = RankingPipeline()

    try:
        result = pipeline.run(
            jd_source=args.jd,
            candidates_source=args.candidates,
            export_csv=True,
            export_json=True,
            display_table=True,
        )

        console.print()
        console.print(
            f"  [bold green]✅ Ranking complete![/bold green] "
            f"Ranked [bold]{result.total_candidates}[/bold] candidates for "
            f"[bold cyan]{result.job_role}[/bold cyan]"
        )

        if result.output_file:
            console.print(
                f"  [bold]📄 Output:[/bold] [link=file://{result.output_file}]{result.output_file}[/link]"
            )
        console.print()

    except FileNotFoundError as e:
        console.print(f"  [bold red]❌ Error:[/bold red] {e}")
        console.print("  Place your data files in the appropriate directories:")
        console.print(f"    Job Descriptions: {settings.job_descriptions_dir}")
        console.print(f"    Candidates:       {settings.candidates_dir}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Pipeline execution failed")
        console.print(f"  [bold red]❌ Pipeline Error:[/bold red] {e}")
        sys.exit(1)

    # ── Step 3: Start FastAPI Server ───────────────────────────────
    if not args.no_server:
        console.print(
            f"  [bold yellow]🚀 Starting FastAPI server on "
            f"http://{args.host}:{args.port}[/bold yellow]"
        )
        console.print(
            f"  [dim]   Docs:   http://localhost:{args.port}/docs[/dim]"
        )
        console.print(
            f"  [dim]   ReDoc:  http://localhost:{args.port}/redoc[/dim]"
        )
        console.print()

        # Share the pipeline instance with FastAPI
        from app.main import set_pipeline
        set_pipeline(pipeline)

        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=False,
            log_level="info",
        )
    else:
        console.print("  [dim]Server skipped (--no-server flag)[/dim]")


if __name__ == "__main__":
    main()
