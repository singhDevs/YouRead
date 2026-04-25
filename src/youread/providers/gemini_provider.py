"""Gemini provider for YouRead."""

from google import genai
from google.genai import types


def call_gemini(
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8000,
    temperature: float = 0.3,
) -> str:
    """Generate text using the Google Gemini API.

    Args:
        api_key: Gemini API key.
        model: Model name (e.g., "gemini-2.5-flash").
        system_prompt: System instructions.
        user_prompt: User input content.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature.

    Returns:
        The generated text.
    """
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        ),
        contents=user_prompt,
    )

    return response.text
