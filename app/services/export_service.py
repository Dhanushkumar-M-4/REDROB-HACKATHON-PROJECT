"""Export service — outputs ranked candidates to CSV, JSON, and console table."""

from pathlib import Path
from typing import List, Optional

import pandas as pd
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.text import Text

from app.models.ranking import RankedCandidate, RankingResult


class ExportService:
    """Exports ranking results to multiple output formats.

    Supports:
        - CSV file export
        - JSON file export
        - Rich console table display
    """

    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()

    def export_csv(
        self,
        ranked_candidates: List[RankedCandidate],
        filename: str = "ranked_candidates.csv",
    ) -> str:
        """Export ranked candidates to CSV.

        Args:
            ranked_candidates: Sorted list of ranked candidates.
            filename: Output CSV filename.

        Returns:
            Path to the exported CSV file.
        """
        output_path = self.output_dir / filename

        records = []
        for rc in ranked_candidates:
            records.append({
                "Rank": rc.rank,
                "Candidate ID": rc.candidate_id,
                "Candidate Name": rc.candidate_name,
                "Semantic Score": rc.semantic_score,
                "LLM Score": rc.llm_score,
                "Experience Score": rc.experience_score,
                "Skill Score": rc.skill_score,
                "Education Score": rc.education_score,
                "Final Score": rc.final_score,
                "Reason": rc.reason,
            })

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=False, encoding="utf-8")

        logger.info("CSV exported │ path={} │ rows={}", output_path, len(records))
        return str(output_path)

    def export_json(
        self,
        ranking_result: RankingResult,
        filename: str = "ranked_candidates.json",
    ) -> str:
        """Export ranking result to JSON.

        Args:
            ranking_result: Complete ranking result.
            filename: Output JSON filename.

        Returns:
            Path to the exported JSON file.
        """
        output_path = self.output_dir / filename

        json_data = ranking_result.model_dump_json(indent=2)
        output_path.write_text(json_data, encoding="utf-8")

        logger.info("JSON exported │ path={}", output_path)
        return str(output_path)

    def display_table(
        self,
        ranked_candidates: List[RankedCandidate],
        title: str = "🏆 AI Candidate Ranking Results",
        top_n: Optional[int] = None,
    ) -> None:
        """Display ranked candidates as a Rich console table.

        Args:
            ranked_candidates: Sorted list of ranked candidates.
            title: Table title.
            top_n: Limit display to top N candidates (None = show all).
        """
        table = Table(
            title=title,
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
            show_lines=True,
            padding=(0, 1),
        )

        # Define columns
        table.add_column("Rank", style="bold yellow", justify="center", width=6)
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Name", style="bold white", width=20)
        table.add_column("Semantic", justify="center", width=10)
        table.add_column("LLM", justify="center", width=10)
        table.add_column("Exp", justify="center", width=8)
        table.add_column("Skills", justify="center", width=8)
        table.add_column("Edu", justify="center", width=8)
        table.add_column("Final", style="bold", justify="center", width=10)
        table.add_column("Reason", width=40, no_wrap=False)

        display_list = ranked_candidates[:top_n] if top_n else ranked_candidates

        for rc in display_list:
            # Color-code the final score
            final_color = self._score_color(rc.final_score)
            final_text = Text(f"{rc.final_score:.1f}", style=f"bold {final_color}")

            table.add_row(
                f"#{rc.rank}",
                rc.candidate_id,
                rc.candidate_name,
                self._score_cell(rc.semantic_score),
                self._score_cell(rc.llm_score),
                self._score_cell(rc.experience_score),
                self._score_cell(rc.skill_score),
                self._score_cell(rc.education_score),
                final_text,
                rc.reason[:80] + "..." if len(rc.reason) > 80 else rc.reason,
            )

        self.console.print()
        self.console.print(table)
        self.console.print()

        # Summary
        if ranked_candidates:
            avg_score = sum(r.final_score for r in ranked_candidates) / len(ranked_candidates)
            self.console.print(
                f"  📊 [bold]Total Candidates:[/bold] {len(ranked_candidates)} │ "
                f"[bold]Avg Score:[/bold] {avg_score:.1f} │ "
                f"[bold]Top Score:[/bold] {ranked_candidates[0].final_score:.1f} │ "
                f"[bold]Bottom Score:[/bold] {ranked_candidates[-1].final_score:.1f}",
            )
            self.console.print()

    @staticmethod
    def _score_cell(score: float) -> Text:
        """Create a color-coded score cell."""
        color = ExportService._score_color(score)
        return Text(f"{score:.1f}", style=color)

    @staticmethod
    def _score_color(score: float) -> str:
        """Get color for a score value."""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        elif score >= 40:
            return "orange3"
        else:
            return "red"
