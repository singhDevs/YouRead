"""Configuration loading and saving utilities."""

import os
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Optional

import yaml
from dotenv import dotenv_values, set_key

from ..providers import PROVIDERS, get_provider_env_var


LLM_CONFIG_DEFAULTS = {
    "model": "gpt-5",
    "max_tokens": 8000,
    "temperature": 0.3,
    "provider": "openai",
}

OUTPUT_CONFIG_DEFAULTS = {
    "directory": "./output",
}

PROCESSING_CONFIG_DEFAULTS = {
    "remove_sponsors": True,
}


@dataclass
class LLMConfig:
    """Configuration for the LLM provider."""
    model: str = "gpt-5"
    max_tokens: int = 8000
    temperature: float = 0.3
    provider: Optional[str] = None


@dataclass
class OutputConfig:
    """Configuration for output settings."""
    directory: Path = field(default_factory=lambda: Path("./output"))


@dataclass
class ProcessingConfig:
    """Configuration for processing settings."""
    remove_sponsors: bool = True


@dataclass
class Config:
    """Application configuration container."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    api_keys: dict[str, str] = field(default_factory=dict)


def get_config_dir() -> Path:
    """Return the per-user config directory for YouRead."""
    if os.name == "nt":
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        base_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    return base_dir / "youread"


def get_config_paths() -> tuple[Path, Path]:
    """Return resolved file paths for user-managed config files.

    Returns:
        Tuple of (settings_yaml_path, dotenv_path).
    """
    config_dir = get_config_dir()
    settings_path = config_dir / "settings.yaml"
    dotenv_path = config_dir / ".env"
    return settings_path, dotenv_path


def _get_default_settings_text() -> str:
    """Read the packaged default settings template."""
    return files("youread").joinpath("config/settings.yaml").read_text(encoding="utf-8")


def ensure_config_files() -> tuple[Path, Path]:
    """Create the user config directory and default settings file if needed."""
    settings_path, dotenv_path = get_config_paths()
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if not settings_path.exists():
        settings_path.write_text(_get_default_settings_text(), encoding="utf-8")

    return settings_path, dotenv_path


def _ensure_private_env_file(dotenv_path: Path) -> None:
    """Create the managed .env file and restrict permissions where possible."""
    if not dotenv_path.exists():
        dotenv_path.touch()

    if os.name != "nt":
        dotenv_path.chmod(0o600)


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from settings.yaml and YouRead's managed .env file.

    Args:
        config_path: Optional path to settings.yaml. If not provided,
                     defaults to the user config directory.

    Returns:
        Config object with all settings loaded.

    Raises:
        FileNotFoundError: If an explicit config_path doesn't exist.
    """
    if config_path is None:
        settings_path, dotenv_path = ensure_config_files()
        config_path = settings_path
    else:
        _, dotenv_path = get_config_paths()

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    api_keys = _load_api_keys(dotenv_path)
    llm_settings = settings.get("llm", {})
    output_settings = settings.get("output", {})
    processing_settings = settings.get("processing", {})

    return Config(
        llm=LLMConfig(
            provider=llm_settings.get("provider", LLM_CONFIG_DEFAULTS["provider"]),
            model=llm_settings.get("model", LLM_CONFIG_DEFAULTS["model"]),
            max_tokens=llm_settings.get("max_tokens", LLM_CONFIG_DEFAULTS["max_tokens"]),
            temperature=llm_settings.get("temperature", LLM_CONFIG_DEFAULTS["temperature"]),
        ),
        output=OutputConfig(
            directory=Path(output_settings.get("directory", OUTPUT_CONFIG_DEFAULTS["directory"])),
        ),
        processing=ProcessingConfig(
            remove_sponsors=processing_settings.get("remove_sponsors", PROCESSING_CONFIG_DEFAULTS["remove_sponsors"]),
        ),
        api_keys=api_keys,
    )


def _load_api_keys(dotenv_path: Path) -> dict[str, str]:
    """Load API keys from YouRead's managed .env file.

    Returns:
        Dictionary of provider name -> API key.
    """
    env_values = dotenv_values(dotenv_path) if dotenv_path.exists() else {}
    api_keys: dict[str, str] = {}
    for provider in PROVIDERS.keys():
        env_var = get_provider_env_var(provider)
        key = env_values.get(env_var)
        if key:
            api_keys[provider] = key
    return api_keys


def get_api_key_for_provider(provider: str, config: Config) -> Optional[str]:
    """Get API key for a specific provider from config.

    Args:
        provider: Provider name (e.g., "openai", "gemini").
        config: Configuration object.

    Returns:
        API key if found, None otherwise.
    """
    return config.api_keys.get(provider)


def check_provider_api_key(provider: str, config: Config) -> bool:
    """Check if API key exists for a provider.

    Args:
        provider: Provider name.
        config: Configuration object.

    Returns:
        True if API key exists, False otherwise.
    """
    return provider in config.api_keys and bool(config.api_keys[provider])


def save_config_values(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    output_directory: Optional[str] = None,
    remove_sponsors: Optional[bool] = None,
    resolved_provider: Optional[str] = None,
) -> None:
    """Persist configuration values to settings.yaml and/or .env.

    Args:
        provider: LLM provider name to save to settings.yaml.
        model: LLM model name to save to settings.yaml.
        max_tokens: Max tokens for LLM response.
        temperature: Temperature for LLM.
        api_key: API key to save to .env.
        output_directory: Output directory path.
        remove_sponsors: Whether to remove sponsor segments.
        resolved_provider: Provider name used to determine the env var
                          name when saving api_key (e.g., "openai" → OPENAI_API_KEY).
    """
    settings_path, dotenv_path = ensure_config_files()

    with open(settings_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    if provider is not None or model is not None or max_tokens is not None or temperature is not None:
        llm_settings = settings.setdefault("llm", {})
        if provider is not None:
            llm_settings["provider"] = provider
        if model is not None:
            llm_settings["model"] = model
        if max_tokens is not None:
            llm_settings["max_tokens"] = max_tokens
        if temperature is not None:
            llm_settings["temperature"] = temperature

    if output_directory is not None:
        output_settings = settings.setdefault("output", {})
        output_settings["directory"] = output_directory

    if remove_sponsors is not None:
        processing_settings = settings.setdefault("processing", {})
        processing_settings["remove_sponsors"] = remove_sponsors

    with open(settings_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, default_flow_style=False, sort_keys=False)

    if api_key is not None and resolved_provider is not None:
        env_var = get_provider_env_var(resolved_provider)
        _ensure_private_env_file(dotenv_path)
        set_key(str(dotenv_path), env_var, api_key)
        _ensure_private_env_file(dotenv_path)


def get_missing_api_keys_message(provider: str) -> str:
    """Generate a user-friendly message to nudge user about missing API key.

    Args:
        provider: The provider that's missing an API key.

    Returns:
        Formatted message string.
    """
    env_var = get_provider_env_var(provider)
    return (
        f"\n[yellow]API Key Missing:[/yellow] No API key found for provider '{provider}'.\n"
        f"Please save your {env_var} to YouRead's managed .env file by running:\n"
        f"  youread config set --provider {provider} --set-api-key\n"
        f"To get an API key, visit:\n"
        f"  - OpenAI: https://platform.openai.com/api-keys\n"
        f"  - Gemini: https://aistudio.google.com/app/apikey"
    )
