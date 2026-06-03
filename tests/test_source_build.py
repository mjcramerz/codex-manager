import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SRC = REPO_ROOT / "src" / "install"
PYTHON_SRC = REPO_ROOT / "src" / "python"
if str(INSTALL_SRC) not in sys.path:
    sys.path.insert(0, str(INSTALL_SRC))
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

import source_build  # noqa: E402


class SourceBuildSettingsTests(unittest.TestCase):
    def test_load_source_build_settings_uses_release_workflow_defaults(self) -> None:
        settings = source_build.load_source_build_settings({})

        self.assertEqual(settings.repo_url, "https://github.com/imjcramer/codex.git")
        self.assertEqual(settings.build_root, Path("/pool/builds/codex"))
        self.assertEqual(settings.cache_root, Path("/pool/cache/codex"))
        self.assertEqual(settings.output_dir, Path("/pool/builds/codex/output"))
        self.assertEqual(settings.checkout_dir, Path(tempfile.gettempdir()) / "codex-source-checkout")

    def test_load_source_build_settings_derives_relative_output_and_checkout(self) -> None:
        settings = source_build.load_source_build_settings(
            {
                "CODEX_SOURCE_REPO_URL": "https://github.com/imjcramer/codex.git",
                "CODEX_SOURCE_BUILD_ROOT": "/tmp/build-root",
                "CODEX_SOURCE_CACHE_ROOT": "/tmp/cache-root",
            }
        )

        self.assertEqual(settings.output_dir, Path("/tmp/build-root/output"))
        self.assertEqual(settings.checkout_dir, Path(tempfile.gettempdir()) / "codex-source-checkout")

    def test_load_source_build_environment_uses_repo_env_and_allows_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".env").write_text(
                "\n".join(
                    [
                        'CODEX_SOURCE_REPO_URL="https://github.com/imjcramer/codex.git"',
                        'CODEX_SOURCE_BUILD_ROOT="/tmp/from-env-file/build"',
                        'CODEX_SOURCE_CACHE_ROOT="/tmp/from-env-file/cache"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"CODEX_SOURCE_BUILD_ROOT": "/tmp/from-process/build"},
                clear=False,
            ):
                env = source_build.load_source_build_environment(repo_root)

        self.assertEqual(env["CODEX_SOURCE_REPO_URL"], "https://github.com/imjcramer/codex.git")
        self.assertEqual(env["CODEX_SOURCE_BUILD_ROOT"], "/tmp/from-process/build")
        self.assertEqual(env["CODEX_SOURCE_CACHE_ROOT"], "/tmp/from-env-file/cache")

    def test_ensure_output_artifact_requires_binaries_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            bin_dir = output_dir / "bin"
            share_dir = output_dir / "share"
            bin_dir.mkdir(parents=True)
            share_dir.mkdir(parents=True)

            binary = bin_dir / "codex"
            binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            binary.chmod(0o755)

            self.assertIsNone(source_build.ensure_output_artifact(output_dir))

            (share_dir / source_build.RELEASE_SCHEMA_FILENAME).write_text("{}", encoding="utf-8")

            self.assertEqual(source_build.ensure_output_artifact(output_dir), output_dir)

    def test_publish_output_alias_rejects_overlapping_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            build_root = Path(tmpdir) / "build"
            published = build_root / "published"
            published.mkdir(parents=True)

            with self.assertRaisesRegex(source_build.SourceBuildError, "must not overlap"):
                source_build._publish_output_alias(build_root, published)

    def test_publish_output_alias_preserves_existing_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            old_published = root / "old"
            new_published = root / "new"
            output = root / "output"
            old_published.mkdir()
            new_published.mkdir()
            marker = old_published / "marker"
            marker.write_text("keep\n", encoding="utf-8")
            output.symlink_to(old_published)

            result = source_build._publish_output_alias(output, new_published)

            self.assertEqual(result, output)
            self.assertTrue(marker.is_file())
            self.assertTrue(output.is_symlink())
            self.assertEqual(output.resolve(strict=True), new_published)


if __name__ == "__main__":
    unittest.main()
