"""LLM provider dispatch for YouRead."""

from ..exceptions import UnsupportedProviderError
from .openai_provider import call_openai
from .gemini_provider import call_gemini


PROVIDERS: dict[str, callable] = {
    "openai": call_openai,
    "gemini": call_gemini,
}

_MODEL_PREFIX_MAP = {
    "gpt-": "openai",
    "o1": "openai",
    "o3": "openai",
    "o4-": "openai",
    "gemini-": "gemini",
}

_PROVIDER_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def get_provider_env_var(provider: str) -> str:
    """Get the environment variable name for a provider's API key.

    Args:
        provider: Provider name (e.g., "openai", "gemini").

    Returns:
        Environment variable name (e.g., "OPENAI_API_KEY").

    Raises:
        UnsupportedProviderError: If provider is not recognized.
    """
    env_var = _PROVIDER_ENV_VARS.get(provider.lower())
    if env_var is None:
        raise UnsupportedProviderError(provider, list(PROVIDERS.keys()))
    return env_var


def infer_provider(model: str) -> str:
    """Infer the LLM provider from the model name.

    Args:
        model: The model identifier (e.g., "gpt-5", "gemini-2.5-flash").

    Returns:
        The provider name (e.g., "openai", "gemini").

    Raises:
        UnsupportedProviderError: If the model name doesn't match any known provider.
    """
    model_lower = model.lower()
    for prefix, provider in _MODEL_PREFIX_MAP.items():
        if model_lower.startswith(prefix):
            return provider

    raise UnsupportedProviderError(
        model,
        list(PROVIDERS.keys()),
    )


def call_llm(
    provider: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8000,
    temperature: float = 0.3,
) -> str:
    """Dispatch an LLM call to the appropriate provider.

    Args:
        provider: Provider name ("openai" or "gemini").
        api_key: API key for the provider.
        model: Model identifier.
        system_prompt: System/instruction prompt.
        user_prompt: User/content prompt.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature.

    Returns:
        The generated text response.

    Raises:
        UnsupportedProviderError: If provider is not recognized.
    """
    fn = PROVIDERS.get(provider)
    if fn is None:
        raise UnsupportedProviderError(provider, list(PROVIDERS.keys()))
    return fn(
        api_key=api_key,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )


__all__ = ["call_llm", "infer_provider", "PROVIDERS", "get_provider_env_var"]