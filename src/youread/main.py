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
from .providers import infer_provider, PROVIDERS, get_provider_env_var
from .exceptions import YouReadError, UnsupportedProviderError
from .utils import (
    extract_video_id,
    load_config,
    save_config_values,
    check_provider_api_key,
    get_missing_api_keys_message,
)


MODE_CHOICES = ["summary", "standard", "detailed"]


app = typer.Typer(
    name="youread",
    help="Convert YouTube videos into comprehensive, readable articles.",
    add_completion=False,
)

config_app = typer.Typer(help="Manage YouRead configuration.")
app.add_typer(config_app, name="config")

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print("[bold]YouRead[/bold] v0.2.0")
        raise typer.Exit()


def open_file(file_path: Path) -> None:
    """Open a file with the system default application."""
    path = str(file_path)

    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=True)
    else:
        subprocess.run(["xdg-open", path], check=True)


def create_progress() -> Progress:
    """Create a terminal-safe progress display.

    Rich's default spinner can fail on some Windows cp1252 consoles when the
    terminal is non-interactive. Fall back to an ASCII-safe spinner in those
    environments so validation errors still render cleanly.
    """
    spinner_name = "dots"
    if console.encoding.lower() != "utf-8" or not console.is_interactive:
        spinner_name = "line"

    return Progress(
        SpinnerColumn(spinner_name=spinner_name),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    )


def _print_config_section(title: str, lines: list[tuple[str, str]]) -> None:
    """Print a config section with consistent formatting."""
    console.print(f"\n[bold]{title}[/bold]")
    console.print("-" * 30)
    for label, value in lines:
        console.print(f"  {label}:  [cyan]{value}[/cyan]")


def _format_bool(value: bool) -> str:
    """Format a boolean for display."""
    return "[green]enabled[/green]" if value else "[red]disabled[/red]"


@config_app.command("show")
def config_show() -> None:
    """Display current YouRead configuration."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print()
    console.print("[bold]YouRead Configuration[/bold]")
    console.print("-" * 30)

    provider_display = config.llm.provider or "(auto-detect from model)"
    _print_config_section("LLM Settings", [
        ("Provider", provider_display),
        ("Model", config.llm.model),
        ("Max Tokens", str(config.llm.max_tokens)),
        ("Temperature", str(config.llm.temperature)),
    ])

    _print_config_section("Output Settings", [
        ("Directory", str(config.output.directory)),
    ])

    _print_config_section("Processing", [
        ("Sponsor Removal", _format_bool(config.processing.remove_sponsors)),
    ])

    console.print(f"\n[bold]API Keys:[/bold]")
    console.print("-" * 30)
    for provider_name in PROVIDERS:
        env_var = get_provider_env_var(provider_name)
        key = config.api_keys.get(provider_name)
        if key:
            console.print(f"  {env_var}:  [green](set)[/green]")
        else:
            console.print(f"  {env_var}:  [dim](not set)[/dim]")
    console.print()


@config_app.command("set")
def config_set(
    provider: Optional[str] = typer.Option(
        None, "--provider",
        help="LLM provider ('openai' or 'gemini').",
    ),
    model: Optional[str] = typer.Option(
        None, "--model",
        help="LLM model name (e.g., 'gpt-5', 'gemini-2.5-flash').",
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens",
        help="Maximum tokens for LLM response.",
    ),
    temperature: Optional[float] = typer.Option(
        None, "--temperature",
        help="LLM sampling temperature (0.0-2.0).",
    ),
    set_api_key: bool = typer.Option(
        False, "--set-api-key",
        help="Prompt securely for an API key for the configured provider.",
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir",
        help="Output directory for articles.",
    ),
    remove_sponsors: Optional[bool] = typer.Option(
        None, "--remove-sponsors/--keep-sponsors",
        help="Enable/disable sponsor segment removal.",
    ),
) -> None:
    """Update YouRead configuration. Settings are persisted to user config files."""
    if (
        provider is None
        and model is None
        and max_tokens is None
        and temperature is None
        and not set_api_key
        and output_dir is None
        and remove_sponsors is None
    ):
        console.print("[yellow]No options provided.[/yellow] Usage examples:")
        console.print("  youread config set --provider openai --model gpt-5")
        console.print("  youread config set --provider openai --set-api-key")
        console.print("  youread config set --provider gemini --model gemini-2.5-flash --set-api-key")
        console.print("\nThen run:  youread run <URL>")
        raise typer.Exit()

    if provider is not None and provider not in PROVIDERS:
        console.print(f"[red]Error:[/red] Unknown provider '{provider}'. Supported: {', '.join(PROVIDERS.keys())}")
        raise typer.Exit(code=1)

    resolved_provider = provider
    if model is not None:
        try:
            inferred = infer_provider(model)
            if resolved_provider is None:
                resolved_provider = inferred
            elif resolved_provider != inferred:
                console.print(
                    f"[red]Error:[/red] Provider mismatch! "
                    f"Model '[cyan]{model}[/cyan]' expects '[cyan]{inferred}[/cyan]' "
                    f"but '--provider {resolved_provider}' was specified.\n"
                    f"Either remove --provider, use --provider {inferred}, or choose a different model."
                )
                raise typer.Exit(code=1)
        except UnsupportedProviderError:
            if resolved_provider is not None:
                console.print(
                    f"[red]Error:[/red] Unknown model '[cyan]{model}[/cyan]' for provider '[cyan]{resolved_provider}[/cyan]'.\n"
                    f"Use a known model like 'gpt-5' (OpenAI) or 'gemini-2.5-flash' (Gemini)."
                )
                raise typer.Exit(code=1)
            else:
                console.print(
                    f"[red]Error:[/red] Unknown model '[cyan]{model}[/cyan]'. Cannot determine provider.\n"
                    f"Please specify --provider explicitly."
                )
                raise typer.Exit(code=1)

    if model is not None and provider is None:
        try:
            provider = infer_provider(model)
        except Exception:
            pass

    resolved_provider = provider
    if set_api_key and resolved_provider is None:
        try:
            config = load_config()
            if config.llm.provider:
                resolved_provider = config.llm.provider
            elif model:
                resolved_provider = infer_provider(model)
            else:
                resolved_provider = infer_provider(config.llm.model)
        except Exception:
            console.print(
                "[red]Error:[/red] Cannot determine provider for API key. "
                "Use --provider to specify which provider this key is for."
            )
            raise typer.Exit(code=1)

    api_key: Optional[str] = None
    if set_api_key:
        if resolved_provider is None:
            console.print(
                "[red]Error:[/red] Cannot determine provider for API key. "
                "Use --provider to specify which provider this key is for."
            )
            raise typer.Exit(code=1)
        api_key = typer.prompt(
            f"Enter {get_provider_env_var(resolved_provider)}",
            hide_input=True,
            confirmation_prompt=True,
        )

    if provider is not None:
        console.print(f"[green]+[/green] Provider set to: [cyan]{provider}[/cyan]")
    if model is not None:
        console.print(f"[green]+[/green] Model set to: [cyan]{model}[/cyan]")
    if max_tokens is not None:
        console.print(f"[green]+[/green] Max tokens set to: [cyan]{max_tokens}[/cyan]")
    if temperature is not None:
        console.print(f"[green]+[/green] Temperature set to: [cyan]{temperature}[/cyan]")
    if output_dir is not None:
        console.print(f"[green]+[/green] Output directory set to: [cyan]{output_dir}[/cyan]")
    if remove_sponsors is not None:
        state = "enabled" if remove_sponsors else "disabled"
        console.print(f"[green]+[/green] Sponsor removal {state}")

    save_config_values(
        provider=provider,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        api_key=api_key,
        output_directory=output_dir,
        remove_sponsors=remove_sponsors,
        resolved_provider=resolved_provider,
    )

    if api_key is not None and resolved_provider:
        env_var = get_provider_env_var(resolved_provider)
        console.print(f"[green]+[/green] {env_var} saved to YouRead's managed .env")

    console.print()
    config_show()


@config_app.command("check")
def config_check() -> None:
    """Check if API key is configured for the current provider."""
    try:
        config = load_config()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    provider = config.llm.provider or infer_provider(config.llm.model)
    has_key = check_provider_api_key(provider, config)

    console.print()
    if has_key:
        console.print(f"[green]OK[/green] API key configured for [cyan]{provider}[/cyan]")
    else:
        env_var = get_provider_env_var(provider)
        console.print(f"[red]X[/red] No API key configured for [cyan]{provider}[/cyan]")
        console.print()
        console.print(f"Set your {env_var} by running:")
        console.print(f"  youread config set --provider {provider} --set-api-key")
        console.print()
        console.print("Get an API key from:")
        if provider == "openai":
            console.print("  https://platform.openai.com/api-keys")
        elif provider == "gemini":
            console.print("  https://aistudio.google.com/app/apikey")
    console.print()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Convert YouTube videos into comprehensive, readable articles."""
    if ctx.invoked_subcommand is None:
        console.print("[bold]YouRead[/bold] — Convert YouTube videos into readable articles.\n")
        console.print("Usage:  youread run <URL> [OPTIONS]")
        console.print("        youread config show")
        console.print("        youread config set [OPTIONS]")
        console.print("        youread config check")
        console.print("\nRun 'youread --help' for details.")
        raise typer.Exit()


@app.command()
def run(
    url: str = typer.Argument(
        ...,
        help="YouTube video URL to convert into an article.",
    ),
    no_sponsorblock: bool = typer.Option(
        False,
        "--no-sponsorblock",
        help="Disable SponsorBlock filtering.",
    ),
    mode: str = typer.Option(
        "standard",
        "--mode", "-m",
        help="Article generation mode: summary (key points only), standard (full coverage), detailed (enhanced with examples).",
    ),
    custom_prompt: Optional[str] = typer.Option(
        None,
        "--prompt", "-p",
        help="Custom instructions to guide article generation (e.g., 'Focus on code examples').",
    ),
    model_override: Optional[str] = typer.Option(
        None,
        "--model",
        help="LLM model to use (e.g., 'gpt-5', 'gemini-2.5-flash'). Overrides config.",
    ),
    provider_override: Optional[str] = typer.Option(
        None,
        "--provider",
        help="LLM provider ('openai' or 'gemini'). Auto-detected from model if omitted.",
    ),
) -> None:
    """Generate a readable article from a YouTube video."""
    try:
        if mode not in MODE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid mode '{mode}'. Choose from: {', '.join(MODE_CHOICES)}")
            raise typer.Exit(code=1)

        config = load_config()

        effective_model = model_override or config.llm.model

        if provider_override:
            effective_provider = provider_override
        elif model_override:
            effective_provider = infer_provider(effective_model)
        elif config.llm.provider:
            effective_provider = config.llm.provider
        else:
            effective_provider = infer_provider(effective_model)

        expected_provider = infer_provider(effective_model)
        if expected_provider != effective_provider:
            console.print(
                f"[red]Error:[/red] Provider mismatch! "
                f"Model '[cyan]{effective_model}[/cyan]' expects '[cyan]{expected_provider}[/cyan]' "
                f"but provider is set to '[cyan]{effective_provider}[/cyan]'.\n"
                f"Either use --provider {expected_provider} or change model in config."
            )
            raise typer.Exit(code=1)

        if check_provider_api_key(effective_provider, config):
            effective_api_key = config.api_keys[effective_provider]
        else:
            console.print(get_missing_api_keys_message(effective_provider))
            raise typer.Exit(code=1)

        output_dir = config.output.directory
        output_dir.mkdir(parents=True, exist_ok=True)

        mode_desc = {"summary": "key points, fast read", "standard": "full coverage, balanced", "detailed": "enhanced with examples"}
        console.print(f"[dim]Mode: {mode} ({mode_desc[mode]})[/dim]")
        console.print(f"[dim]Provider: {effective_provider} | Model: {effective_model}[/dim]")
        if custom_prompt:
            console.print(f"[dim]Custom: {custom_prompt[:50]}{'...' if len(custom_prompt) > 50 else ''}[/dim]")

        with create_progress() as progress:
            task = progress.add_task("Parsing YouTube URL...", total=None)
            video_id = extract_video_id(url)
            progress.remove_task(task)
        console.print(f"[green]+[/green] Video ID: [cyan]{video_id}[/cyan]")

        with create_progress() as progress:
            task = progress.add_task("Fetching video metadata...", total=None)
            video_info = fetch_video_metadata(video_id)
            progress.remove_task(task)
        console.print(f"[green]+[/green] Title: [cyan]{video_info.title}[/cyan]")
        console.print(f"[green]+[/green] Channel: [cyan]{video_info.channel}[/cyan]")

        languages = ["en"]
        with create_progress() as progress:
            task = progress.add_task("Fetching transcript...", total=None)
            segments = fetch_transcript(video_id, languages=languages)
            progress.remove_task(task)
        console.print(f"[green]+[/green] Retrieved [cyan]{len(segments):,}[/cyan] transcript segments")

        use_sponsorblock = config.processing.remove_sponsors and not no_sponsorblock
        if use_sponsorblock:
            with create_progress() as progress:
                task = progress.add_task("Checking for sponsor segments...", total=None)
                sponsor_segments = fetch_sponsor_segments(video_id)
                progress.remove_task(task)

            if sponsor_segments:
                original_count = len(segments)
                segments = remove_sponsor_segments(segments, sponsor_segments)
                removed_count = original_count - len(segments)
                console.print(f"[green]+[/green] Removed [yellow]{removed_count}[/yellow] sponsored segments")
            else:
                console.print(f"[green]+[/green] No sponsor segments found")

        full_text = transcript_to_text(segments)
        word_count = len(full_text.split())
        console.print(f"[green]+[/green] Transcript word count: [cyan]{word_count:,}[/cyan]")

        with create_progress() as progress:
            task = progress.add_task(f"Generating article with {effective_provider}/{effective_model}...", total=None)
            article = generate_article(
                transcript_text=full_text,
                video_info=video_info,
                provider=effective_provider,
                api_key=effective_api_key,
                video_id=video_id,
                model=effective_model,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
                mode=mode,
                custom_prompt=custom_prompt,
            )
            progress.remove_task(task)
        console.print(f"[green]+[/green] Article generated successfully")

        filename = sanitize_filename(video_info.title) + ".md"
        output_path = output_dir / filename

        output_path.write_text(article, encoding="utf-8")
        console.print(f"[green]+[/green] Saved to: [cyan]{output_path}[/cyan]")

        console.print()
        if typer.confirm("Open the article?", default=False):
            open_file(output_path)
            console.print("[dim]Opening file...[/dim]")

        console.print("\n[bold green]Done![/bold green]")

    except YouReadError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
