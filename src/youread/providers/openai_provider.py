"""OpenAI provider for YouRead."""

from typing import Optional

from openai import OpenAI
from openai import APIError


def call_openai(
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    """Generate text using the OpenAI API.

    Optional parameters (max_tokens, temperature) are sent to the API
    only when the caller provides them.  If the chosen model rejects
    a parameter, the provider retries without it before raising.

    Args:
        api_key: OpenAI API key.
        model: Model name (e.g., "gpt-5").
        system_prompt: System instructions.
        user_prompt: User input content.
        max_tokens: Maximum response tokens (model-dependent).
        temperature: Sampling temperature (model-dependent).

    Returns:
        The generated text.
    """
    client = OpenAI(api_key=api_key)

    kwargs: dict = dict(
        model=model,
        instructions=system_prompt,
        input=user_prompt,
    )

    opt_params: dict[str, object] = {}
    if max_tokens is not None:
        opt_params["max_output_tokens"] = max_tokens
    if temperature is not None:
        opt_params["temperature"] = temperature

    kwargs.update(opt_params)
    fallback_keys = list(opt_params.keys())

    response = _call_responses(client, kwargs, fallback_keys)
    return response.output_text


def _call_responses(
    client: OpenAI,
    kwargs: dict,
    fallback_keys: list[str],
) -> object:
    """Call responses.create, retrying if the model rejects a parameter.

    Each retry drops the most recently added fallback key so that
    calls can succeed even when the model doesn't support a given
    optional parameter.

    Args:
        client: OpenAI client instance.
        kwargs: Keyword arguments for the API call.
        fallback_keys: Ordered list of keys that may be unsupported.
                       The last key is removed first on failure.

    Returns:
        The API response object.
    """
    total = len(fallback_keys)
    for attempt in range(total + 1):
        try:
            return client.responses.create(**kwargs)
        except APIError as e:
            if attempt < total and e.status_code == 400:
                key = fallback_keys.pop()
                kwargs.pop(key, None)
                continue
            raise

    raise RuntimeError("OpenAI API call failed after retrying without optional parameters")
