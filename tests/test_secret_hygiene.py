import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from youread.utils.config import save_config_values


FORBIDDEN_ARCHIVE_NAMES = {
    ".env",
    ".pypirc",
}


class SecretHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base_path = Path(self.temp_dir.name)
        self.settings_path = self.base_path / "settings.yaml"
        self.dotenv_path = self.base_path / ".env"
        self.settings_path.write_text("{}\n", encoding="utf-8")

    def patch_paths(self):
        return patch(
            "youread.utils.config.get_config_paths",
            return_value=(self.settings_path, self.dotenv_path),
        )

    def test_api_key_is_not_written_to_settings_yaml(self) -> None:
        with self.patch_paths():
            save_config_values(api_key="super-secret", resolved_provider="openai")

        settings_text = self.settings_path.read_text(encoding="utf-8")
        dotenv_text = self.dotenv_path.read_text(encoding="utf-8")

        self.assertNotIn("super-secret", settings_text)
        self.assertNotIn("OPENAI_API_KEY", settings_text)
        self.assertIn("OPENAI_API_KEY", dotenv_text)
        self.assertIn("super-secret", dotenv_text)

    def test_managed_env_file_is_private_on_posix(self) -> None:
        chmod_calls: list[int] = []

        original_chmod = Path.chmod

        def record_chmod(path: Path, mode: int) -> None:
            chmod_calls.append(mode)
            return original_chmod(path, mode)

        with (
            self.patch_paths(),
            patch("youread.utils.config.os.name", "posix"),
            patch("pathlib.Path.chmod", new=record_chmod),
        ):
            save_config_values(api_key="super-secret", resolved_provider="openai")

        self.assertIn(0o600, chmod_calls)

    def test_root_gitignore_blocks_secret_files(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", gitignore)
        self.assertIn("*.env", gitignore)
        self.assertIn(".env.*", gitignore)

    def test_manifest_explicitly_excludes_secret_and_local_artifact_paths(self) -> None:
        manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("exclude .env", manifest)
        self.assertIn("exclude .env.*", manifest)
        self.assertIn("global-exclude *.env", manifest)
        self.assertIn("prune dist", manifest)
        self.assertIn("prune build", manifest)
        self.assertIn("prune venv", manifest)

    def test_existing_wheel_does_not_contain_secret_files(self) -> None:
        wheel_paths = sorted((ROOT / "dist").glob("*.whl"))
        if not wheel_paths:
            self.skipTest("No wheel artifact present in dist/")

        with zipfile.ZipFile(wheel_paths[-1]) as wheel_file:
            names = wheel_file.namelist()

        self._assert_archive_names_are_safe(names)

    def test_existing_sdist_does_not_contain_secret_files(self) -> None:
        sdist_paths = sorted((ROOT / "dist").glob("*.tar.gz"))
        if not sdist_paths:
            self.skipTest("No sdist artifact present in dist/")

        with tarfile.open(sdist_paths[-1], "r:gz") as sdist_file:
            names = sdist_file.getnames()

        self._assert_archive_names_are_safe(names)

    def test_repository_tracked_files_do_not_include_secret_files(self) -> None:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        tracked_files = {
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip()
        }

        self.assertNotIn(".env", tracked_files)
        self.assertNotIn(".pypirc", tracked_files)

    def _assert_archive_names_are_safe(self, names: list[str]) -> None:
        normalized_names = {Path(name).name for name in names}
        self.assertTrue(FORBIDDEN_ARCHIVE_NAMES.isdisjoint(normalized_names))
        self.assertFalse(any(name.endswith(".env") for name in names))
        self.assertFalse(any("/.env" in name.replace("\\", "/") for name in names))


if __name__ == "__main__":
    unittest.main()
