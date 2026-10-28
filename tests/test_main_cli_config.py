import sys
import subprocess
import tempfile
from contextlib import ExitStack
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from typer.testing import CliRunner

from youread.main import app, open_file
from youread.models import TranscriptSegment, VideoInfo
from youread.utils.config import Config, LLMConfig, OutputConfig, ProcessingConfig


def build_config(
    *,
    provider: str = "openai",
    model: str = "gpt-5",
    api_keys: dict[str, str] | None = None,
    remove_sponsors: bool = True,
    output_directory: Path | None = None,
) -> Config:
    return Config(
        llm=LLMConfig(provider=provider, model=model, max_tokens=8000, temperature=0.3),
        output=OutputConfig(directory=output_directory or Path("./output")),
        processing=ProcessingConfig(remove_sponsors=remove_sponsors),
        api_keys=api_keys or {},
    )


class MainCliConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def invoke_run_with_stubbed_services(
        self,
        *,
        title: str = "Sample Title",
        open_prompt_input: str = "n\n",
        open_file_side_effect=None,
        open_file_return_value: bool = True,
        launcher_side_effect=None,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            config = build_config(
                api_keys={"openai": "secret"},
                remove_sponsors=False,
                output_directory=output_dir,
            )

            with ExitStack() as stack:
                stack.enter_context(patch("youread.main.load_config", return_value=config))
                stack.enter_context(patch("youread.main.extract_video_id", return_value="abc123def45"))
                stack.enter_context(
                    patch(
                        "youread.main.fetch_video_metadata",
                        return_value=VideoInfo(video_id="abc123def45", title=title, channel="Chan"),
                    )
                )
                stack.enter_context(
                    patch(
                        "youread.main.fetch_transcript",
                        return_value=[TranscriptSegment(text="hello world", start=0.0, duration=1.0)],
                    )
                )
                stack.enter_context(patch("youread.main.transcript_to_text", return_value="hello world"))
                stack.enter_context(patch("youread.main.generate_article", return_value="# article"))

                open_file_mock = None
                if launcher_side_effect is not None:
                    stack.enter_context(patch("youread.main.sys.platform", "linux"))
                    stack.enter_context(patch("youread.main.subprocess.run", side_effect=launcher_side_effect))
                else:
                    open_file_mock = stack.enter_context(
                        patch(
                            "youread.main.open_file",
                            return_value=open_file_return_value,
                            side_effect=open_file_side_effect,
                        )
                    )

                result = self.runner.invoke(
                    app,
                    ["run", "https://youtube.com/watch?v=abc123def45"],
                    input=open_prompt_input,
                )

            files = list(output_dir.glob("*.md"))
            content = files[0].read_text(encoding="utf-8") if files else ""
            return result, files, content, open_file_mock

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

    def test_run_open_prompt_declined_exits_success_and_saves_article(self) -> None:
        result, files, content, open_file_mock = self.invoke_run_with_stubbed_services(open_prompt_input="n\n")

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(files), 1)
        self.assertEqual(content, "# article")
        open_file_mock.assert_not_called()

    def test_run_open_prompt_success_prints_opening_message(self) -> None:
        result, files, content, open_file_mock = self.invoke_run_with_stubbed_services(
            open_prompt_input="y\n",
            open_file_return_value=True,
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(files), 1)
        self.assertEqual(content, "# article")
        self.assertIn("Opening file...", result.stdout)
        open_file_mock.assert_called_once()

    def test_run_open_prompt_filenotfound_shows_manual_hint_and_exits_success(self) -> None:
        result, files, content, open_file_mock = self.invoke_run_with_stubbed_services(
            open_prompt_input="y\n",
            launcher_side_effect=FileNotFoundError(),
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(files), 1)
        self.assertEqual(content, "# article")
        self.assertIn("Could not open file automatically.", result.stdout)
        self.assertIn("Open it manually at:", result.stdout)
        self.assertIsNone(open_file_mock)

    def test_run_open_prompt_calledprocesserror_shows_manual_hint_and_exits_success(self) -> None:
        result, files, content, open_file_mock = self.invoke_run_with_stubbed_services(
            open_prompt_input="y\n",
            launcher_side_effect=subprocess.CalledProcessError(1, ["xdg-open", "article.md"]),
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(files), 1)
        self.assertEqual(content, "# article")
        self.assertIn("Could not open file automatically.", result.stdout)
        self.assertIn("Open it manually at:", result.stdout)
        self.assertIsNone(open_file_mock)

    def test_run_saves_article_for_long_multibyte_title(self) -> None:
        result, files, content, _ = self.invoke_run_with_stubbed_services(
            title="अ" * 100,
            open_prompt_input="n\n",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(files), 1)
        self.assertEqual(content, "# article")
        self.assertLessEqual(len(files[0].name.encode("utf-8")), 255)


class OpenFileTests(unittest.TestCase):
    def test_open_file_uses_xdg_open_on_linux(self) -> None:
        path = Path("article.md")
        with (
            patch("youread.main.sys.platform", "linux"),
            patch("youread.main.subprocess.run") as run_mock,
        ):
            result = open_file(path)

        self.assertTrue(result)
        run_mock.assert_called_once_with(["xdg-open", str(path)], check=True)

    def test_open_file_returns_false_if_xdg_open_unavailable(self) -> None:
        path = Path("article.md")
        with (
            patch("youread.main.sys.platform", "linux"),
            patch("youread.main.subprocess.run", side_effect=FileNotFoundError),
        ):
            result = open_file(path)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
