import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from youread.exceptions import UnsupportedProviderError
from youread.providers import call_llm, get_provider_env_var, infer_provider
from youread.utils.config import (
    check_provider_api_key,
    get_api_key_for_provider,
    get_config_dir,
    get_missing_api_keys_message,
    load_config,
    save_config_values,
)


class ConfigUtilsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base_path = Path(self.temp_dir.name)
        self.system_path_cls = type(Path())
        self.settings_path = self.base_path / "settings.yaml"
        self.dotenv_path = self.base_path / ".env"

    def write_settings(self, content: str) -> None:
        self.settings_path.write_text(content, encoding="utf-8")

    def patch_paths(self):
        return patch(
            "youread.utils.config.get_config_paths",
            return_value=(self.settings_path, self.dotenv_path),
        )

    def test_load_config_uses_defaults_and_managed_dotenv_api_keys(self) -> None:
        self.write_settings("{}\n")
        self.dotenv_path.write_text(
            'OPENAI_API_KEY="openai-secret"\nGEMINI_API_KEY="gemini-secret"\n',
            encoding="utf-8",
        )

        with (
            self.patch_paths(),
        ):
            config = load_config()

        self.assertEqual(config.llm.provider, "openai")
        self.assertEqual(config.llm.model, "gpt-5")
        self.assertEqual(config.llm.max_tokens, 8000)
        self.assertEqual(config.llm.temperature, 0.3)
        self.assertEqual(config.output.directory, Path("./output"))
        self.assertTrue(config.processing.remove_sponsors)
        self.assertEqual(config.api_keys["openai"], "openai-secret")
        self.assertEqual(config.api_keys["gemini"], "gemini-secret")

    def test_load_config_reads_yaml_values(self) -> None:
        self.write_settings(
            "\n".join(
                [
                    "llm:",
                    "  provider: gemini",
                    "  model: gemini-2.5-flash",
                    "  max_tokens: 4096",
                    "  temperature: 0.8",
                    "output:",
                    "  directory: ./articles",
                    "processing:",
                    "  remove_sponsors: false",
                    "",
                ]
            )
        )

        with (
            self.patch_paths(),
        ):
            config = load_config()

        self.assertEqual(config.llm.provider, "gemini")
        self.assertEqual(config.llm.model, "gemini-2.5-flash")
        self.assertEqual(config.llm.max_tokens, 4096)
        self.assertEqual(config.llm.temperature, 0.8)
        self.assertEqual(config.output.directory, Path("./articles"))
        self.assertFalse(config.processing.remove_sponsors)
        self.assertEqual(config.api_keys, {})

    def test_load_config_bootstraps_default_settings_file(self) -> None:
        with (
            self.patch_paths(),
            patch(
                "youread.utils.config._get_default_settings_text",
                return_value="llm:\n  provider: openai\n",
            ),
        ):
            config = load_config()

        self.assertTrue(self.settings_path.exists())
        self.assertEqual(config.llm.provider, "openai")

    def test_save_config_values_persists_yaml_and_dotenv(self) -> None:
        self.write_settings("{}\n")

        with self.patch_paths():
            save_config_values(
                provider="gemini",
                model="gemini-2.5-flash",
                max_tokens=2048,
                temperature=0.6,
                api_key="gemini-secret",
                output_directory="./generated",
                remove_sponsors=False,
                resolved_provider="gemini",
            )

        yaml_text = self.settings_path.read_text(encoding="utf-8")
        dotenv_text = self.dotenv_path.read_text(encoding="utf-8")

        self.assertIn("provider: gemini", yaml_text)
        self.assertIn("model: gemini-2.5-flash", yaml_text)
        self.assertIn("max_tokens: 2048", yaml_text)
        self.assertIn("temperature: 0.6", yaml_text)
        self.assertIn("directory: ./generated", yaml_text)
        self.assertIn("remove_sponsors: false", yaml_text)
        self.assertIn("GEMINI_API_KEY", dotenv_text)
        self.assertIn("gemini-secret", dotenv_text)

    def test_check_provider_api_key_and_get_api_key_for_provider(self) -> None:
        self.write_settings("{}\n")
        self.dotenv_path.write_text('OPENAI_API_KEY="openai-secret"\n', encoding="utf-8")

        with (
            self.patch_paths(),
        ):
            config = load_config()

        self.assertTrue(check_provider_api_key("openai", config))
        self.assertFalse(check_provider_api_key("gemini", config))
        self.assertEqual(get_api_key_for_provider("openai", config), "openai-secret")
        self.assertIsNone(get_api_key_for_provider("gemini", config))

    def test_get_missing_api_keys_message_uses_secure_prompt_flow(self) -> None:
        message = get_missing_api_keys_message("gemini")
        self.assertIn("GEMINI_API_KEY", message)
        self.assertIn("--set-api-key", message)
        self.assertNotIn("--api-key <", message)

    def test_load_config_ignores_ambient_environment_variables(self) -> None:
        self.write_settings("{}\n")

        with (
            self.patch_paths(),
            patch.dict(os.environ, {"OPENAI_API_KEY": "ambient-secret"}, clear=True),
        ):
            config = load_config()

        self.assertEqual(config.api_keys, {})

    def test_get_config_dir_ignores_empty_appdata_on_windows(self) -> None:
        with (
            patch("youread.utils.config.os.name", "nt"),
            patch("youread.utils.config.sys.platform", "win32"),
            patch.dict(os.environ, {"APPDATA": ""}, clear=True),
            patch("youread.utils.config.Path.home", return_value=self.system_path_cls("C:/Users/tester")),
        ):
            config_dir = get_config_dir()

        self.assertEqual(config_dir, Path("C:/Users/tester/AppData/Roaming/youread"))

    def test_get_config_dir_ignores_empty_xdg_config_home(self) -> None:
        with (
            patch("youread.utils.config.os.name", "posix"),
            patch("youread.utils.config.sys.platform", "linux"),
            patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}, clear=True),
            patch("youread.utils.config.Path.home", return_value=self.system_path_cls("C:/Users/tester")),
        ):
            config_dir = get_config_dir()

        self.assertEqual(config_dir, Path("C:/Users/tester/.config/youread"))

    def test_get_config_dir_uses_xdg_config_home_on_linux(self) -> None:
        with (
            patch("youread.utils.config.os.name", "posix"),
            patch("youread.utils.config.sys.platform", "linux"),
            patch.dict(os.environ, {"XDG_CONFIG_HOME": "/home/tester/.xdg-config"}, clear=True),
        ):
            config_dir = get_config_dir()

        self.assertEqual(config_dir, Path("/home/tester/.xdg-config/youread"))


class ProviderHelperTests(unittest.TestCase):
    def test_infer_provider_supports_known_prefixes(self) -> None:
        self.assertEqual(infer_provider("gpt-5"), "openai")
        self.assertEqual(infer_provider("o1-preview"), "openai")
        self.assertEqual(infer_provider("o3-mini"), "openai")
        self.assertEqual(infer_provider("o4-mini"), "openai")
        self.assertEqual(infer_provider("gemini-2.5-flash"), "gemini")

    def test_infer_provider_raises_for_unknown_model(self) -> None:
        with self.assertRaises(UnsupportedProviderError):
            infer_provider("claude-sonnet")

    def test_get_provider_env_var_is_case_insensitive(self) -> None:
        self.assertEqual(get_provider_env_var("OPENAI"), "OPENAI_API_KEY")
        self.assertEqual(get_provider_env_var("gemini"), "GEMINI_API_KEY")

    def test_get_provider_env_var_raises_for_unknown_provider(self) -> None:
        with self.assertRaises(UnsupportedProviderError):
            get_provider_env_var("anthropic")

    def test_call_llm_dispatches_to_provider_function(self) -> None:
        def fake_provider(**kwargs):
            return f"{kwargs['model']}::{kwargs['temperature']}"

        with patch.dict("youread.providers.PROVIDERS", {"openai": fake_provider}, clear=True):
            result = call_llm(
                provider="openai",
                api_key="secret",
                model="gpt-5",
                system_prompt="system",
                user_prompt="user",
                max_tokens=123,
                temperature=0.9,
            )

        self.assertEqual(result, "gpt-5::0.9")

    def test_call_llm_raises_for_unsupported_provider(self) -> None:
        with self.assertRaises(UnsupportedProviderError):
            call_llm(
                provider="anthropic",
                api_key="secret",
                model="claude",
                system_prompt="system",
                user_prompt="user",
            )


if __name__ == "__main__":
    unittest.main()
