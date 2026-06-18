"""Custom exceptions for YouRead."""


class YouReadError(Exception):
    """Base exception for all YouRead errors."""
    pass


class InvalidURLError(YouReadError):
    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__(f"Invalid YouTube URL: {url}")


class TranscriptNotFoundError(YouReadError):
    def __init__(self, video_id: str) -> None:
        self.video_id = video_id
        super().__init__(f"No transcript available for video: {video_id}")


class VideoNotFoundError(YouReadError):
    def __init__(self, video_id: str) -> None:
        self.video_id = video_id
        super().__init__(f"Video not found or unavailable: {video_id}")


class UnsupportedProviderError(YouReadError):
    def __init__(self, provider: str, supported: list[str]) -> None:
        self.provider = provider
        self.supported = supported
        super().__init__(
            f"Unsupported provider '{provider}'. "
            f"Supported: {', '.join(supported)}"
        )


class APIKeyMissingError(YouReadError):
    def __init__(self, provider: str) -> None:
        self.provider = provider
        env_var = f"{provider.upper()}_API_KEY"
        super().__init__(
            f"API key for '{provider}' not found. "
            f"Save {env_var} to YouRead's managed .env file, or use: "
            f"youread config set --provider {provider} --set-api-key"
        )
