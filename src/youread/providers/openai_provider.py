"""OpenAI provider for YouRead."""

from openai import OpenAI


def call_openai(
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8000,
    temperature: float = 0.3,
) -> str:
    """Generate text using the OpenAI API.

    Args:
        api_key: OpenAI API key.
        model: Model name (e.g., "gpt-5").
        system_prompt: System instructions.
        user_prompt: User input content.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature.

    Returns:
        The generated text.
    """
    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=max_tokens,
        temperature=temperature,
    )

    return response.output_text
