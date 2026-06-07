import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from typer.testing import CliRunner

from youread.main import app
from youread.utils.config import Config, LLMConfig, OutputConfig, ProcessingConfig


def build_config(
    *,
    provider: str = "openai",
    model: str = "gpt-5",
    api_keys: dict[str, str] | None = None,
    remove_sponsors: bool = True,
) -> Config:
    return Config(
        llm=LLMConfig(provider=provider, model=model, max_tokens=8000, temperature=0.3),
        output=OutputConfig(directory=Path("./output")),
        processing=ProcessingConfig(remove_sponsors=remove_sponsors),
        api_keys=api_keys or {},
    )


class MainCliConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_config_show_does_not_expose_api_key_material(self) -> None:
        config = build_config(api_keys={"openai": "sk-super-secret-value"})

        with patch("youread.main.load_config", return_value=config):
            result = self.runner.invoke(app, ["config", "show"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("OPENAI_API_KEY:  (set)", result.stdout)
        self.assertNotIn("sk-super-secret-value", result.stdout)

    def test_config_set_help_uses_secure_api_key_prompt(self) -> None:
        result = self.runner.invoke(
            app,
            ["config", "set", "--help"],
            env={"TYPER_USE_RICH": "0"},
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--set-api-key", result.stdout)
        self.assertNotIn("--api-key", result.stdout)

    def test_config_set_without_options_shows_secure_examples(self) -> None:
        result = self.runner.invoke(app, ["config", "set"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--set-api-key", result.stdout)
        self.assertNotIn("--api-key <", result.stdout)

    def test_config_set_rejects_provider_model_mismatch(self) -> None:
        result = self.runner.invoke(
            app, ["config", "set", "--provider", "gemini", "--model", "gpt-5"]
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Provider mismatch!", result.stdout)

    def test_config_set_rejects_unknown_model_for_provider(self) -> None:
        result = self.runner.invoke(
            app, ["config", "set", "--provider", "openai", "--model", "nonsense-model"]
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Unknown model", result.stdout)

    def test_config_set_rejects_unknown_model_without_provider(self) -> None:
        result = self.runner.invoke(app, ["config", "set", "--model", "nonsense-model"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Cannot determine provider", result.stdout)

    def test_config_set_secure_prompt_saves_without_echoing_secret(self) -> None:
        with (
            patch("youread.main.save_config_values") as save_config_values,
            patch("youread.main.config_show"),
        ):
            result = self.runner.invoke(
                app,
                ["config", "set", "--provider", "openai", "--set-api-key"],
                input="super-secret-value\nsuper-secret-value\n",
            )

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("super-secret-value", result.stdout)
        self.assertEqual(save_config_values.call_args.kwargs["api_key"], "super-secret-value")

    def test_config_check_missing_key_uses_secure_guidance(self) -> None:
        with patch("youread.main.load_config", return_value=build_config(api_keys={})):
            result = self.runner.invoke(app, ["config", "check"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--set-api-key", result.stdout)
        self.assertNotIn("--api-key", result.stdout)

    def test_run_rejects_provider_model_mismatch(self) -> None:
        config = build_config(api_keys={"openai": "secret"})

        with patch("youread.main.load_config", return_value=config):
            result = self.runner.invoke(
                app,
                [
                    "run",
                    "invalid-url",
                    "--model",
                    "gemini-2.5-flash",
                    "--provider",
                    "openai",
                ],
            )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Provider mismatch!", result.stdout)

    def test_run_missing_key_uses_secure_guidance(self) -> None:
        config = build_config(api_keys={})

        with patch("youread.main.load_config", return_value=config):
            result = self.runner.invoke(app, ["run", "invalid-url", "--model", "gemini-2.5-flash"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("API Key Missing", result.stdout)
        self.assertIn("--set-api-key", result.stdout)

    def test_run_invalid_url_returns_clean_error(self) -> None:
        config = build_config(api_keys={"openai": "secret"})

        with patch("youread.main.load_config", return_value=config):
            result = self.runner.invoke(app, ["run", "invalid-url"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Invalid YouTube URL: invalid-url", result.stdout)
        self.assertNotIn("Unexpected error", result.stdout)


if __name__ == "__main__":
    unittest.main()
