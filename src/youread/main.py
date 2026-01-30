"""YouRead CLI - Convert YouTube videos into readable articles."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .transcript import fetch_transcript, transcript_to_text
from .metadata import fetch_video_metadata, sanitize_filename
from .sponsorblock import fetch_sponsor_segments, remove_sponsor_segments
from .article_generator import generate_article, ArticleMode
from .utils import extract_video_id, load_config
from .exceptions import YouReadError


# Valid mode choices for CLI
MODE_CHOICES = ["summary", "standard", "detailed"]


app = typer.Typer(
    name="youread",
    help="Convert YouTube videos into comprehensive, readable articles.",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print("[bold]YouRead[/bold] v0.1.0")
        raise typer.Exit()


def open_file(file_path: Path) -> None:
    """Open a file with the system default application."""
    path = str(file_path)

    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=True)
    else:  # Linux
        subprocess.run(["xdg-open", path], check=True)


@app.command()
def main(
    url: str = typer.Argument(
        ...,
        help="YouTube video URL to convert into an article.",
    ),
    language: Optional[str] = typer.Option(
        "en",
        "--language", "-l",
        help="Preferred transcript language code (e.g., 'en', 'es', 'fr').",
    ),
    no_sponsorblock: bool = typer.Option(
        False,
        "--no-sponsorblock",
        help="Disable SponsorBlock filtering.",
    ),
    mode: str = typer.Option(
        "standard",
        "--mode", "-m",
        help="Article generation mode: summary (~30% read time), standard (~50-60%), detailed (~80-90%).",
    ),
    custom_prompt: Optional[str] = typer.Option(
        None,
        "--prompt", "-p",
        help="Custom instructions to guide article generation (e.g., 'Focus on code examples').",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Convert a YouTube video into a readable article.

    Takes a YouTube URL, extracts the transcript, and generates
    a comprehensive markdown article using Gemini.
    """
    try:
        # Validate mode
        if mode not in MODE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Choose from: {', '.join(MODE_CHOICES)}")
            raise typer.Exit(code=1)

        # Load configuration
        config = load_config()

        # Ensure output directory exists
        output_dir = config.output.directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Display mode
        mode_desc = {"summary": "~30% read time", "standard": "~50-60% read time", "detailed": "~80-90% read time"}
        console.print(f"[dim]Mode: {mode} ({mode_desc[mode]})[/dim]")
        if custom_prompt:
            console.print(f"[dim]Custom: {custom_prompt[:50]}{'...' if len(custom_prompt) > 50 else ''}[/dim]")

        # Step 1: Extract video ID from URL
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Parsing YouTube URL...", total=None)
            video_id = extract_video_id(url)
            progress.remove_task(task)
        console.print(f"[green]✓[/green] Video ID: [cyan]{video_id}[/cyan]")

        # Step 2: Fetch video metadata
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching video metadata...", total=None)
            video_info = fetch_video_metadata(video_id)
            progress.remove_task(task)
        console.print(f"[green]✓[/green] Title: [cyan]{video_info.title}[/cyan]")
        console.print(f"[green]✓[/green] Channel: [cyan]{video_info.channel}[/cyan]")

        # Step 3: Fetch transcript
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            languages = [language] if language else ["en"]
            task = progress.add_task("Fetching transcript...", total=None)
            segments = fetch_transcript(video_id, languages=languages)
            progress.remove_task(task)
        console.print(f"[green]✓[/green] Retrieved [cyan]{len(segments):,}[/cyan] transcript segments")

        # Step 4: Fetch and remove sponsor segments
        if not no_sponsorblock:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Checking for any sponsor segments...", total=None)
                sponsor_segments = fetch_sponsor_segments(video_id)
                progress.remove_task(task)

            if sponsor_segments:
                original_count = len(segments)
                segments = remove_sponsor_segments(segments, sponsor_segments)
                removed_count = original_count - len(segments)
                console.print(f"[green]✓[/green] Removed [yellow]{removed_count}[/yellow] sponsored segments")
            else:
                console.print(f"[green]✓[/green] No sponsor segments found")

        # Step 5: Convert to text
        full_text = transcript_to_text(segments)
        word_count = len(full_text.split())
        console.print(f"[green]✓[/green] Transcript word count: [cyan]{word_count:,}[/cyan]")

        # Step 6: Generate article with Gemini
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating article with Gemini...", total=None)
            article = generate_article(
                transcript_text=full_text,
                video_info=video_info,
                api_key=config.gemini_api_key,
                video_id=video_id,
                model=config.llm.model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                mode=mode,
                custom_prompt=custom_prompt,
            )
            progress.remove_task(task)
        console.print(f"[green]✓[/green] Article generated successfully")

        # Step 7: Save article to file
        filename = sanitize_filename(video_info.title) + ".md"
        output_path = output_dir / filename

        output_path.write_text(article, encoding="utf-8")
        console.print(f"[green]✓[/green] Saved to: [cyan]{output_path}[/cyan]")

        # Step 8: Prompt to open file
        console.print()
        if typer.confirm("Open the article?", default=False):
            open_file(output_path)
            console.print("[dim]Opening file...[/dim]")

        console.print("\n[bold green]Done![/bold green]")

    except YouReadError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
