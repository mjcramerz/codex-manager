from __future__ import annotations

import os
from pathlib import Path

MAX_REMOVE_DIR_SCAN = 100_000


def _can_access(path: Path, mode: int) -> bool:
    try:
        return os.access(path, mode)
    except OSError:
        return False


def _tree_has_removal_access(path: Path, max_dirs: int = MAX_REMOVE_DIR_SCAN) -> bool:
    scanned = 0
    try:
        iterator = os.walk(path, topdown=True, followlinks=False)
    except OSError:
        return False

    for current_root, _, _ in iterator:
        scanned += 1
        if scanned > max_dirs:
            # Be conservative on very large trees and require sudo.
            return False
        if not _can_access(Path(current_root), os.W_OK | os.X_OK):
            return False
    return True


def nearest_existing_parent(path: Path) -> Path:
    current = path
    while True:
        try:
            if current.exists():
                return current
        except OSError:
            # Keep walking upward until we can evaluate a known parent.
            pass
        parent = current.parent
        if parent == current:
            break
        current = parent
    return current


def needs_sudo_write(path: Path) -> bool:
    try:
        exists = path.exists()
    except OSError:
        return True

    if exists:
        try:
            if path.is_dir():
                return not _can_access(path, os.W_OK | os.X_OK)
        except OSError:
            return True
        return not _can_access(path, os.W_OK)

    parent = nearest_existing_parent(path.parent)
    return not _can_access(parent, os.W_OK | os.X_OK)


def needs_sudo_remove(path: Path) -> bool:
    parent = nearest_existing_parent(path.parent)
    if not _can_access(parent, os.W_OK | os.X_OK):
        return True
    try:
        exists = path.exists()
    except OSError:
        return True
    if not exists:
        return False
    try:
        is_dir = path.is_dir()
    except OSError:
        return True
    if is_dir:
        if not _can_access(path, os.W_OK | os.X_OK):
            return True
        if not _tree_has_removal_access(path):
            return True
    return False
