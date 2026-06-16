import os
import subprocess
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
    def test_load_source_build_settings_requires_repo_url_and_uses_path_defaults(self) -> None:
        settings = source_build.load_source_build_settings(
            {
                "CODEX_SOURCE_REPO_URL": "https://github.com/mjcramerz/codex.git",
                "CODEX_SOURCE_BASE_REF": "mcr/main",
            }
        )

        self.assertEqual(settings.repo_url, "https://github.com/mjcramerz/codex.git")
        self.assertEqual(settings.build_root, Path("/pool/builds/codex"))
        self.assertEqual(settings.cache_root, Path("/pool/cache/codex"))
        self.assertEqual(settings.output_dir, Path("/pool/builds/codex/output"))
        self.assertEqual(settings.checkout_dir, Path(tempfile.gettempdir()) / "codex-source-checkout")
        self.assertEqual(settings.base_ref, "mcr/main")

    def test_load_source_build_settings_derives_relative_output_and_checkout(self) -> None:
        settings = source_build.load_source_build_settings(
            {
                "CODEX_SOURCE_REPO_URL": "https://github.com/mjcramerz/codex.git",
                "CODEX_SOURCE_BASE_REF": "mcr/main",
                "CODEX_SOURCE_BUILD_ROOT": "/tmp/build-root",
                "CODEX_SOURCE_CACHE_ROOT": "/tmp/cache-root",
            }
        )

        self.assertEqual(settings.output_dir, Path("/tmp/build-root/output"))
        self.assertEqual(settings.checkout_dir, Path(tempfile.gettempdir()) / "codex-source-checkout")

    def test_load_source_build_settings_requires_repo_url(self) -> None:
        with self.assertRaisesRegex(source_build.SourceBuildError, "missing required source-build setting: CODEX_SOURCE_REPO_URL"):
            source_build.load_source_build_settings({})

    def test_load_source_build_environment_uses_repo_env_and_allows_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".env").write_text(
                "\n".join(
                    [
                        'CODEX_SOURCE_REPO_URL="https://github.com/mjcramerz/codex.git"',
                        'CODEX_SOURCE_BASE_REF="mcr/main"',
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

        self.assertEqual(env["CODEX_SOURCE_REPO_URL"], "https://github.com/mjcramerz/codex.git")
        self.assertEqual(env["CODEX_SOURCE_BASE_REF"], "mcr/main")
        self.assertEqual(env["CODEX_SOURCE_BUILD_ROOT"], "/tmp/from-process/build")
        self.assertEqual(env["CODEX_SOURCE_CACHE_ROOT"], "/tmp/from-env-file/cache")

    def test_ensure_source_checkout_repoints_origin_and_syncs_configured_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            checkout_dir = Path(tmpdir) / "checkout"
            (checkout_dir / ".git").mkdir(parents=True)
            for path in source_build._expected_checkout_paths(checkout_dir):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ok\n", encoding="utf-8")

            settings = source_build.SourceBuildSettings(
                repo_url="https://github.com/mjcramerz/codex.git",
                build_root=Path("/tmp/build-root"),
                cache_root=Path("/tmp/cache-root"),
                output_dir=Path("/tmp/output-root"),
                checkout_dir=checkout_dir,
                base_ref="mcr/main",
            )

            def run_checked_side_effect(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                label = kwargs["label"]
                if label == "read source checkout origin url":
                    return subprocess.CompletedProcess(args, 0, stdout="https://github.com/legacy-owner/codex.git\n", stderr="")
                if label == "inspect source checkout state":
                    return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

            with patch.object(source_build, "_run_checked", side_effect=run_checked_side_effect) as run_checked:
                result = source_build.ensure_source_checkout(settings)

        self.assertEqual(result, checkout_dir)
        self.assertEqual(
            [call.kwargs["label"] for call in run_checked.call_args_list],
            [
                "read source checkout origin url",
                "update source checkout origin url",
                "inspect source checkout state",
                "fetch source ref mcr/main",
                "checkout source ref mcr/main",
            ],
        )

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

    def test_read_patch_series_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            series_path = Path(tmpdir) / "patches" / "release" / "series"
            series_path.parent.mkdir(parents=True)
            series_path.write_text("../escape.patch\n", encoding="utf-8")

            with self.assertRaisesRegex(source_build.SourceBuildError, "unsafe release patch series entry"):
                source_build._read_patch_series(series_path)

    def test_build_from_settings_runs_source_script_from_checkout_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkout_dir = root / "checkout"
            script_path = checkout_dir / "scripts" / "release" / "build-codex.sh"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            output_dir = root / "output"
            published_dir = root / "published"
            settings = source_build.SourceBuildSettings(
                repo_url="https://github.com/mjcramerz/codex.git",
                build_root=root / "build",
                cache_root=root / "cache",
                output_dir=output_dir,
                checkout_dir=checkout_dir,
                base_ref="mcr/main",
            )

            with (
                patch.object(source_build, "ensure_source_checkout", return_value=checkout_dir),
                patch.object(source_build, "_run_checked") as run_checked,
                patch.object(source_build, "_resolve_latest_build_dir", return_value=published_dir),
                patch.object(source_build, "_generate_patched_schema"),
                patch.object(source_build, "_publish_output_alias", return_value=output_dir),
                patch.object(source_build, "discover_release_binaries", return_value=[output_dir / "bin" / "codex"]),
            ):
                source_build.build_from_settings(settings)

        build_call = next(
            call
            for call in run_checked.call_args_list
            if call.kwargs.get("label") == "build codex from source"
        )
        self.assertEqual(build_call.kwargs["cwd"], checkout_dir)
        self.assertEqual(
            build_call.args[0],
            [
                "bash",
                str(script_path),
                "--base-ref",
                "mcr/main",
                "--build-root",
                str(settings.build_root),
                "--cache-root",
                str(settings.cache_root),
            ],
        )


if __name__ == "__main__":
    unittest.main()
