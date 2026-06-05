from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from common import parse_env_file
from lib.release_assets import ReleaseAssetError
from lib.release_assets import discover_release_binaries

SOURCE_REPO_URL_KEY = "CODEX_SOURCE_REPO_URL"
SOURCE_BUILD_ROOT_KEY = "CODEX_SOURCE_BUILD_ROOT"
SOURCE_CACHE_ROOT_KEY = "CODEX_SOURCE_CACHE_ROOT"
SOURCE_OUTPUT_DIR_KEY = "CODEX_SOURCE_OUTPUT_DIR"
SOURCE_CHECKOUT_DIR_KEY = "CODEX_SOURCE_CHECKOUT_DIR"
SOURCE_BASE_REF_KEY = "CODEX_SOURCE_BASE_REF"

DEFAULT_SOURCE_REPO_URL = "https://github.com/imjcramer/codex.git"
DEFAULT_BUILD_ROOT = Path("/pool/builds/codex")
DEFAULT_CACHE_ROOT = Path("/pool/cache/codex")
DEFAULT_OUTPUT_DIRNAME = "output"
DEFAULT_CHECKOUT_DIRNAME = "codex-source-checkout"
RELEASE_SCHEMA_FILENAME = "config.schema.json"
BUILD_TIMEOUT_SECONDS = 8 * 60 * 60
SCHEMA_TIMEOUT_SECONDS = 8 * 60 * 60
MAX_ERROR_OUTPUT_CHARS = 2000


class SourceBuildError(RuntimeError):
    """Raised when source-build orchestration fails."""


@dataclass(frozen=True)
class SourceBuildSettings:
    repo_url: str
    build_root: Path
    cache_root: Path
    output_dir: Path
    checkout_dir: Path
    base_ref: str | None


@dataclass(frozen=True)
class SourceBuildResult:
    settings: SourceBuildSettings
    output_dir: Path
    published_dir: Path
    schema_path: Path
    binaries: list[Path]


def _normalize(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _normalize_lexical(path: Path) -> Path:
    return Path(os.path.normpath(str(path.expanduser())))


def _same_or_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _trim_error_output(value: str) -> str:
    rendered = value.strip()
    if len(rendered) <= MAX_ERROR_OUTPUT_CHARS:
        return rendered
    return rendered[:MAX_ERROR_OUTPUT_CHARS].rstrip() + "..."


def _run_checked(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int,
    label: str,
    stream_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd) if cwd is not None else None,
            check=False,
            capture_output=not stream_output,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SourceBuildError(f"{label} timed out after {timeout} seconds") from exc
    if proc.returncode == 0:
        return proc

    if stream_output:
        raise SourceBuildError(f"{label} failed with exit code {proc.returncode}")

    stderr = _trim_error_output(proc.stderr)
    stdout = _trim_error_output(proc.stdout)
    details = stderr or stdout
    if details:
        raise SourceBuildError(f"{label} failed: {details}")
    raise SourceBuildError(f"{label} failed with exit code {proc.returncode}")


def _require_env_value(env: dict[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise SourceBuildError(f"missing required source-build setting: {key}")
    if "\n" in value or "\r" in value or "\x00" in value:
        raise SourceBuildError(f"source-build setting {key} contains control characters")
    return value


def _require_absolute_path(key: str, value: str, *, follow_symlinks: bool = True) -> Path:
    if any(ch.isspace() for ch in value):
        raise SourceBuildError(f"source-build setting {key} contains whitespace: {value}")
    path = Path(value)
    if not path.is_absolute():
        raise SourceBuildError(f"source-build setting {key} must be absolute: {value}")
    if follow_symlinks:
        return _normalize(path)
    return _normalize_lexical(path)


def _require_https_url(key: str, value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SourceBuildError(f"source-build setting {key} must use https: {value}")
    return value


def load_source_build_environment(repo_root: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if isinstance(key, str) and isinstance(value, str)
    }
    env_path = repo_root / ".env"
    if env_path.is_file():
        file_env = parse_env_file(env_path)
        # Explicit shell exports override repo-local .env values.
        merged = dict(file_env)
        merged.update({key: value for key, value in env.items() if key.startswith("CODEX_")})
        return merged
    return env


def load_source_build_settings(env: dict[str, str]) -> SourceBuildSettings:
    repo_url = _require_https_url(
        SOURCE_REPO_URL_KEY,
        env.get(SOURCE_REPO_URL_KEY, "").strip() or DEFAULT_SOURCE_REPO_URL,
    )
    build_root = _require_absolute_path(
        SOURCE_BUILD_ROOT_KEY,
        env.get(SOURCE_BUILD_ROOT_KEY, "").strip() or str(DEFAULT_BUILD_ROOT),
    )
    cache_root = _require_absolute_path(
        SOURCE_CACHE_ROOT_KEY,
        env.get(SOURCE_CACHE_ROOT_KEY, "").strip() or str(DEFAULT_CACHE_ROOT),
    )
    output_dir_raw = env.get(SOURCE_OUTPUT_DIR_KEY, "").strip()
    checkout_dir_raw = env.get(SOURCE_CHECKOUT_DIR_KEY, "").strip()
    base_ref = env.get(SOURCE_BASE_REF_KEY, "").strip() or None
    output_dir = _require_absolute_path(
        SOURCE_OUTPUT_DIR_KEY,
        output_dir_raw or str(build_root / DEFAULT_OUTPUT_DIRNAME),
        follow_symlinks=False,
    )
    checkout_dir = _require_absolute_path(
        SOURCE_CHECKOUT_DIR_KEY,
        checkout_dir_raw or str(Path(tempfile.gettempdir()) / DEFAULT_CHECKOUT_DIRNAME),
    )
    return SourceBuildSettings(
        repo_url=repo_url,
        build_root=build_root,
        cache_root=cache_root,
        output_dir=output_dir,
        checkout_dir=checkout_dir,
        base_ref=base_ref,
    )


def _expected_checkout_paths(checkout_dir: Path) -> tuple[Path, ...]:
    return (
        checkout_dir / "codex-rs" / "Cargo.toml",
        checkout_dir / "scripts" / "release" / "build-codex.sh",
        checkout_dir / "patches" / "release" / "series",
        checkout_dir / "justfile",
    )


def _missing_checkout_paths(checkout_dir: Path) -> tuple[Path, ...]:
    missing = []
    if not (checkout_dir / ".git").exists():
        missing.append(checkout_dir / ".git")
    missing.extend(path for path in _expected_checkout_paths(checkout_dir) if not path.exists())
    return tuple(missing)


def _checkout_is_usable(checkout_dir: Path) -> bool:
    return not _missing_checkout_paths(checkout_dir)


def ensure_source_checkout(settings: SourceBuildSettings) -> Path:
    checkout_dir = settings.checkout_dir
    checkout_dir.parent.mkdir(parents=True, exist_ok=True)

    if _checkout_is_usable(checkout_dir):
        _run_checked(
            ["git", "-C", str(checkout_dir), "fetch", "--prune", "origin"],
            timeout=300,
            label="refresh source checkout",
        )
        return checkout_dir

    if checkout_dir.exists():
        missing = ", ".join(str(path) for path in _missing_checkout_paths(checkout_dir))
        raise SourceBuildError(
            f"configured source checkout path exists but is unusable: {checkout_dir}"
            f" (missing: {missing})"
        )

    _run_checked(
        ["git", "clone", settings.repo_url, str(checkout_dir)],
        timeout=BUILD_TIMEOUT_SECONDS,
        label="clone source repository",
    )
    if not _checkout_is_usable(checkout_dir):
        missing = ", ".join(str(path) for path in _missing_checkout_paths(checkout_dir))
        raise SourceBuildError(f"cloned source checkout is missing expected files: {missing}")
    return checkout_dir


def _resolve_patch_series_entry(series_path: Path, line: str) -> Path:
    if "\x00" in line:
        raise SourceBuildError(f"release patch series entry contains NUL: {series_path}")
    candidate = Path(line)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SourceBuildError(f"unsafe release patch series entry in {series_path}: {line}")
    release_dir = _normalize_lexical(series_path.parent)
    patch_path = _normalize_lexical(release_dir / candidate)
    if not _same_or_within(patch_path, release_dir):
        raise SourceBuildError(f"unsafe release patch series entry in {series_path}: {line}")
    return patch_path


def _read_patch_series(series_path: Path) -> list[Path]:
    patches: list[Path] = []
    for raw_line in series_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patches.append(_resolve_patch_series_entry(series_path, line))
    if not patches:
        raise SourceBuildError(f"no release patches listed in {series_path}")
    return patches


def _generate_patched_schema(
    checkout_dir: Path,
    destination: Path,
) -> None:
    destination = _normalize(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="codex-source-schema-") as tmp_dir:
        worktree_dir = Path(tmp_dir) / "worktree"
        _run_checked(
            ["git", "-C", str(checkout_dir), "worktree", "add", "--detach", str(worktree_dir), "HEAD"],
            timeout=300,
            label="create temporary schema worktree",
        )
        try:
            release_dir = checkout_dir / "patches" / "release"
            for patch_path in _read_patch_series(release_dir / "series"):
                patch_name = str(patch_path.relative_to(release_dir))
                if not patch_path.is_file():
                    raise SourceBuildError(f"release patch not found: {patch_path}")
                _run_checked(
                    [
                        "git",
                        "-C",
                        str(worktree_dir),
                        "apply",
                        "--exclude=patches/release/ROLLOUT*",
                        "--exclude=patches/release/rollouts/*",
                        str(patch_path),
                    ],
                    timeout=300,
                    label=f"apply release patch {patch_name}",
                )
            _run_checked(
                ["just", "write-config-schema"],
                cwd=worktree_dir,
                timeout=SCHEMA_TIMEOUT_SECONDS,
                label="generate patched config.schema.json",
            )
            schema_source = worktree_dir / "codex-rs" / "core" / RELEASE_SCHEMA_FILENAME
            if not schema_source.is_file():
                raise SourceBuildError(f"patched schema was not written: {schema_source}")
            shutil.copyfile(schema_source, destination)
        finally:
            subprocess.run(
                ["git", "-C", str(checkout_dir), "worktree", "remove", str(worktree_dir), "--force"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )


def _resolve_latest_build_dir(build_root: Path) -> Path:
    latest_link = build_root / "latest"
    if latest_link.exists():
        resolved = latest_link.resolve(strict=False)
        if resolved.is_dir():
            return resolved

    candidates = sorted(
        (
            path
            for path in build_root.iterdir()
            if path.is_dir() and (path / "build-manifest.json").is_file()
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    raise SourceBuildError(f"unable to locate built source artifacts under {build_root}")


def _publish_output_alias(output_dir: Path, published_dir: Path) -> Path:
    output_path = _normalize_lexical(output_dir)
    published_path = _normalize(published_dir)
    output_resolved = output_path.resolve(strict=False)

    if output_resolved == published_path:
        return output_path
    if _same_or_within(published_path, output_resolved) or _same_or_within(output_resolved, published_path):
        raise SourceBuildError(
            f"{SOURCE_OUTPUT_DIR_KEY} must not overlap published source build directory: "
            f"{output_path} vs {published_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.is_symlink() or output_path.is_file():
        output_path.unlink()
    elif output_path.is_dir():
        shutil.rmtree(output_path)
    output_path.symlink_to(published_path)
    return output_path


def ensure_output_artifact(output_dir: Path) -> Path | None:
    resolved = _normalize(output_dir)
    if not resolved.exists():
        return None
    try:
        binaries = discover_release_binaries(resolved)
    except (ReleaseAssetError, RuntimeError):
        return None
    if not binaries:
        return None
    schema_path = resolved / "share" / RELEASE_SCHEMA_FILENAME
    if not schema_path.is_file():
        return None
    return resolved


def _resolved_base_ref(settings: SourceBuildSettings, checkout_dir: Path) -> str:
    if settings.base_ref:
        return settings.base_ref
    proc = _run_checked(
        ["git", "-C", str(checkout_dir), "symbolic-ref", "--quiet", "--short", "HEAD"],
        timeout=60,
        label="resolve source checkout HEAD",
    )
    ref = proc.stdout.strip()
    return ref or "HEAD"


def build_from_settings(settings: SourceBuildSettings) -> SourceBuildResult:
    print(f"[build] source repository: {settings.repo_url}")
    print(f"[build] checkout root: {settings.checkout_dir}")
    print(f"[build] build root: {settings.build_root}")
    print(f"[build] cache root: {settings.cache_root}")
    print(f"[build] published output alias: {settings.output_dir}")
    checkout_dir = ensure_source_checkout(settings)
    build_root = settings.build_root
    cache_root = settings.cache_root
    script_path = checkout_dir / "scripts" / "release" / "build-codex.sh"
    if not script_path.is_file():
        raise SourceBuildError(f"source build script not found: {script_path}")

    print(f"[build] invoking source build script: {script_path}")
    _run_checked(
        [
            "bash",
            str(script_path),
            "--base-ref",
            _resolved_base_ref(settings, checkout_dir),
            "--build-root",
            str(build_root),
            "--cache-root",
            str(cache_root),
        ],
        cwd=checkout_dir,
        timeout=BUILD_TIMEOUT_SECONDS,
        label="build codex from source",
        stream_output=True,
    )

    published_dir = _resolve_latest_build_dir(build_root)
    schema_path = published_dir / "share" / RELEASE_SCHEMA_FILENAME
    print(f"[build] generating patched schema snapshot: {schema_path}")
    _generate_patched_schema(checkout_dir, schema_path)
    output_alias = _publish_output_alias(settings.output_dir, published_dir)
    print(f"[build] published artifacts: {published_dir}")
    print(f"[build] output alias updated: {output_alias}")

    try:
        binaries = discover_release_binaries(output_alias)
    except (ReleaseAssetError, RuntimeError) as exc:
        raise SourceBuildError(str(exc)) from exc
    print("[build] discovered binaries: " + ", ".join(binary.name for binary in binaries))

    return SourceBuildResult(
        settings=settings,
        output_dir=output_alias,
        published_dir=published_dir,
        schema_path=schema_path,
        binaries=binaries,
    )


def build_if_missing(settings: SourceBuildSettings) -> SourceBuildResult:
    existing = ensure_output_artifact(settings.output_dir)
    if existing is not None:
        binaries = discover_release_binaries(existing)
        return SourceBuildResult(
            settings=settings,
            output_dir=existing,
            published_dir=existing.resolve(strict=False),
            schema_path=existing / "share" / RELEASE_SCHEMA_FILENAME,
            binaries=binaries,
        )
    return build_from_settings(settings)
