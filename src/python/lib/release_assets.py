from __future__ import annotations

from pathlib import Path
import stat

MAX_RELEASE_SCAN_ENTRIES = 50_000


class ReleaseAssetError(RuntimeError):
    """Raised when release binaries cannot be discovered safely."""


def _iter_regular_files(root: Path, max_entries: int) -> list[tuple[Path, int]]:
    scanned = 0
    out: list[tuple[Path, int]] = []
    for candidate in sorted(root.rglob("*")):
        scanned += 1
        if scanned > max_entries:
            raise ReleaseAssetError(
                f"release package scan exceeded limit ({max_entries} entries)"
            )
        try:
            metadata = candidate.lstat()
        except OSError as exc:
            raise ReleaseAssetError(f"failed to stat release candidate {candidate}: {exc}") from exc
        if not stat.S_ISREG(metadata.st_mode):
            continue
        out.append((candidate, metadata.st_mode))
    return out


def discover_release_binaries(
    extract_root: Path,
    *,
    max_entries: int = MAX_RELEASE_SCAN_ENTRIES,
) -> list[Path]:
    if max_entries <= 0:
        raise ReleaseAssetError("max_entries must be > 0")
    if not extract_root.is_dir():
        raise ReleaseAssetError(f"release extract root is not a directory: {extract_root}")

    bin_exec_candidates: list[Path] = []
    fallback_exec_candidates: list[Path] = []
    for candidate, mode in _iter_regular_files(extract_root, max_entries=max_entries):
        rel_parts = candidate.relative_to(extract_root).parts
        if candidate.name.startswith(".") or any(part.startswith(".") for part in rel_parts):
            continue
        if not (mode & 0o111):
            continue
        if "bin" not in rel_parts[:-1]:
            fallback_exec_candidates.append(candidate)
        else:
            bin_exec_candidates.append(candidate)

    candidates = bin_exec_candidates
    if not candidates:
        candidates = fallback_exec_candidates

    if not candidates:
        raise ReleaseAssetError("release package does not contain executable binaries")

    by_name: dict[str, list[Path]] = {}
    for path in candidates:
        by_name.setdefault(path.name, []).append(path)
    for name, paths in sorted(by_name.items()):
        if len(paths) <= 1:
            continue
        rendered = ", ".join(str(path.relative_to(extract_root)) for path in paths)
        raise ReleaseAssetError(
            f"release package contains duplicate binary name '{name}': {rendered}"
        )

    return [by_name[name][0] for name in sorted(by_name.keys())]
