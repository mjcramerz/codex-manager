from __future__ import annotations

from pathlib import Path
from pathlib import PurePosixPath
import tarfile

MAX_TAR_MEMBERS = 10_000
MAX_TAR_TOTAL_BYTES = 5 * 1024 * 1024 * 1024


class ArchiveSafetyError(RuntimeError):
    """Raised when archive extraction would violate safety constraints."""


def _validate_member_name(name: str) -> None:
    if not name:
        raise ArchiveSafetyError("archive member name cannot be empty")
    if "\x00" in name or "\\" in name:
        raise ArchiveSafetyError(f"archive member name is invalid: {name!r}")
    if name.startswith("/"):
        raise ArchiveSafetyError(f"archive member path must be relative: {name!r}")
    parts = PurePosixPath(name).parts
    if any(part == ".." for part in parts):
        raise ArchiveSafetyError(f"archive member path traverses outside destination: {name!r}")


def _validated_members(
    tf: tarfile.TarFile,
    max_members: int,
    max_total_bytes: int,
) -> list[tarfile.TarInfo]:
    members = tf.getmembers()
    if len(members) > max_members:
        raise ArchiveSafetyError(
            f"archive has too many entries ({len(members)} > {max_members})"
        )

    total_bytes = 0
    validated: list[tarfile.TarInfo] = []
    for member in members:
        _validate_member_name(member.name)
        if member.isdev() or member.isfifo():
            raise ArchiveSafetyError(f"archive member type is not allowed: {member.name!r}")
        if member.issym() or member.islnk():
            raise ArchiveSafetyError(f"archive links are not allowed: {member.name!r}")
        if member.isfile():
            size = int(member.size)
            if size < 0:
                raise ArchiveSafetyError(f"archive member has negative size: {member.name!r}")
            total_bytes += size
            if total_bytes > max_total_bytes:
                raise ArchiveSafetyError(
                    f"archive exceeds max extracted size ({total_bytes} > {max_total_bytes})"
                )
        elif not member.isdir():
            raise ArchiveSafetyError(
                f"archive member type is unsupported for extraction: {member.name!r}"
            )
        validated.append(member)
    return validated


def safe_extractall(
    tf: tarfile.TarFile,
    destination: Path,
    *,
    max_members: int = MAX_TAR_MEMBERS,
    max_total_bytes: int = MAX_TAR_TOTAL_BYTES,
) -> None:
    if max_members <= 0:
        raise ArchiveSafetyError("max_members must be > 0")
    if max_total_bytes <= 0:
        raise ArchiveSafetyError("max_total_bytes must be > 0")

    members = _validated_members(tf, max_members=max_members, max_total_bytes=max_total_bytes)
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ArchiveSafetyError(f"failed to prepare extraction directory: {exc}") from exc
    try:
        tf.extractall(destination, members=members, filter="data")
    except TypeError:
        # Python < 3.12 has no extraction filter support.
        try:
            tf.extractall(destination, members=members)
        except (tarfile.TarError, OSError) as exc:
            raise ArchiveSafetyError(f"failed to extract archive: {exc}") from exc
    except (tarfile.TarError, OSError) as exc:
        raise ArchiveSafetyError(f"failed to extract archive: {exc}") from exc
