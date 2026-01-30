"""Article generation using Gemini API."""

import math

from google import genai
from google.genai import types
from pathlib import Path
from typing import Optional, Literal
from importlib.resources import files

from .models import VideoInfo


# Valid mode choices
ArticleMode = Literal["summary", "standard", "detailed"]

# Reading speed for technical content (words per minute)
# 150 WPM is realistic for technical/educational material requiring comprehension
TECHNICAL_WPM = 150


def calculate_reading_time(text: str, wpm: int = TECHNICAL_WPM) -> str:
    """Calculate reading time from text content.

    Args:
        text: The article text to measure.
        wpm: Words per minute reading speed.

    Returns:
        Formatted reading time string (e.g., "~5 min read").
    """
    # Count words (split on whitespace)
    word_count = len(text.split())

    # Calculate minutes, round up to nearest minute
    minutes = math.ceil(word_count / wpm)

    return f"~{minutes} min read"


def insert_reading_time(article: str) -> str:
    """Replace the reading time placeholder with calculated reading time.

    Args:
        article: The generated article with READING_TIME_PLACEHOLDER.

    Returns:
        Article with accurate reading time inserted.
    """
    reading_time = calculate_reading_time(article)
    return article.replace("READING_TIME_PLACEHOLDER", reading_time)


def load_prompt(prompt_path: Optional[Path] = None) -> str:
    """Load a prompt from file.

    Args:
        prompt_path: Path to the prompt file. Defaults to prompts/system_prompt_v2.md.

    Returns:
        The prompt content as a string.
    """
    if prompt_path is None:
        prompt_path = files("youread.prompts") / "system_prompt_v2.md"

    if hasattr(prompt_path, 'read_text'):
        return prompt_path.read_text(encoding="utf-8")

    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return path.read_text(encoding="utf-8")


def load_mode_prompt(mode: ArticleMode) -> str:
    """Load the mode-specific prompt fragment.

    Args:
        mode: The article generation mode (summary, standard, detailed).

    Returns:
        The mode prompt content as a string.
    """
    mode_path = files("youread.prompts.modes") / f"{mode}.md"

    if hasattr(mode_path, 'read_text'):
        return mode_path.read_text(encoding="utf-8")

    path = Path(mode_path)
    if not path.exists():
        raise FileNotFoundError(f"Mode prompt file not found: {mode_path}")

    return path.read_text(encoding="utf-8")


def compose_system_prompt(
    mode: ArticleMode = "standard",
    custom_prompt: Optional[str] = None,
    video_id: Optional[str] = None,
) -> str:
    """Compose the full system prompt from base + mode + custom.

    Args:
        mode: The article generation mode.
        custom_prompt: Optional user-provided custom instructions.
        video_id: Optional video ID for constructing the source URL.

    Returns:
        The composed system prompt.
    """
    # Load base prompt
    base_prompt = load_prompt()

    # Load mode-specific instructions
    mode_instructions = load_mode_prompt(mode)

    # Replace the mode placeholder
    prompt = base_prompt.replace("{{MODE_INSTRUCTIONS}}", mode_instructions)

    # Replace video URL placeholder if video_id provided
    if video_id:
        video_url = f"https://youtube.com/watch?v={video_id}"
        prompt = prompt.replace("VIDEO_URL_PLACEHOLDER", video_url)

    # Append custom prompt if provided
    if custom_prompt:
        custom_section = f"""
<custom_instructions>
The user has provided the following additional instructions. Follow them while maintaining the core quality standards:

{custom_prompt}
</custom_instructions>
"""
        prompt += custom_section

    return prompt


def generate_article(
    transcript_text: str,
    video_info: VideoInfo,
    api_key: str,
    video_id: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 8000,
    temperature: float = 0.3,
    mode: ArticleMode = "standard",
    custom_prompt: Optional[str] = None,
) -> str:
    """Generate a readable article from a video transcript using Gemini.

    Args:
        transcript_text: The full transcript text.
        video_info: Video metadata (title, channel).
        api_key: Gemini API key.
        video_id: Video ID for source link.
        model: Gemini model to use.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (0.0-1.0).
        mode: Article generation mode (summary, standard, detailed).
        custom_prompt: Optional custom instructions from user.

    Returns:
        The generated article as markdown text.

    Raises:
        Exception: If the API call fails.
    """
    # Configure the API
    client = genai.Client(api_key=api_key)

    # Compose the system prompt
    system_prompt = compose_system_prompt(
        mode=mode,
        custom_prompt=custom_prompt,
        video_id=video_id,
    )

    # Build the user prompt with context
    user_prompt = f"""## Video Information
**Title:** {video_info.title}
**Channel:** {video_info.channel}

## Transcript
{transcript_text}
"""

    # Generate the article with specified config
    response = client.models.generate_content(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature),
        contents=user_prompt
    )

    # Calculate and insert accurate reading time
    article = insert_reading_time(response.text)

    return article
