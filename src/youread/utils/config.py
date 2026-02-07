"""Configuration loading utilities."""

from importlib.resources import files
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the LLM (Gemini API)."""
    model: str
    max_tokens: int
    temperature: float


@dataclass(frozen=True)
class OutputConfig:
    """Configuration for output settings."""
    directory: Path


@dataclass(frozen=True)
class Config:
    """Application configuration container."""
    output: OutputConfig
    llm: LLMConfig
    llm_api_key: str


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from settings.yaml and environment variables.

    Args:
        config_path: Optional path to settings.yaml. If not provided,
                     defaults to config/settings.yaml relative to project root.

    Returns:
        Config object with all settings loaded.

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist.
        ValueError: If GPT_API_KEY is not set.
    """
    # Load .env file
    load_dotenv()

    # Determine config file path
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = files("youread.config") / "settings.yaml"


    # Load YAML settings
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)

    # Get API key from environment
    api_key = os.getenv("GPT_API_KEY")
    if not api_key:
        raise ValueError(
            "GPT_API_KEY not found. "
            "Please set it in your .env file or environment variables."
        )

    # Build config objects
    output_settings = settings.get("output", {})
    llm_settings = settings.get("llm", {})

    return Config(
        output=OutputConfig(
            directory=Path(output_settings.get("directory", "./output"))
        ),
        llm=LLMConfig(
            model=llm_settings.get("model", "gpt-5.2"),
            max_tokens=llm_settings.get("max_tokens", 8000),
            temperature=llm_settings.get("temperature", 0.3),
        ),
        llm_api_key=api_key,
    )
