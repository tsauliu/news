"""
Utility helpers for the AutoNews pipeline.

Currently includes helpers for archiving existing contents in a target
output directory to a subfolder named 'SS' before generating new outputs.
"""

from __future__ import annotations

import os
import shutil
import datetime as dt


def _unique_destination_path(dest_dir: str, name: str) -> str:
    """Return a destination path under `dest_dir` that avoids collisions.

    If `dest_dir/name` exists, append a timestamp suffix. If that also exists,
    append a numeric counter until a free path is found.
    """
    base, ext = os.path.splitext(name)
    candidate = os.path.join(dest_dir, name)
    if not os.path.exists(candidate):
        return candidate

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = os.path.join(dest_dir, f"{base}_{timestamp}{ext}")
    if not os.path.exists(candidate):
        return candidate

    i = 1
    while True:
        candidate = os.path.join(dest_dir, f"{base}_{timestamp}_{i}{ext}")
        if not os.path.exists(candidate):
            return candidate
        i += 1


def archive_existing_in_target(target_dir: str, ss_name: str = "SS") -> None:
    """Move existing files/subfolders in `target_dir` into `target_dir/ss_name`.

    - Creates `target_dir` and `target_dir/ss_name` if missing.
    - Skips moving the `ss_name` directory itself.
    - On name collisions under `ss_name`, appends a timestamp (and counter) to
      the destination name to avoid overwriting previous archives.
    """
    if not target_dir:
        return

    os.makedirs(target_dir, exist_ok=True)
    ss_dir = os.path.join(target_dir, ss_name)
    os.makedirs(ss_dir, exist_ok=True)

    try:
        entries = os.listdir(target_dir)
    except FileNotFoundError:
        return

    for name in entries:
        if name == ss_name:
            continue
        # Skip obvious hidden files that shouldn't be archived (optional)
        if name.startswith('.'):
            continue

        src_path = os.path.join(target_dir, name)
        # Only move direct children
        dest_path = _unique_destination_path(ss_dir, name)
        try:
            shutil.move(src_path, dest_path)
            print(f"Archived '{src_path}' -> '{dest_path}'")
        except Exception as e:
            print(f"Warning: failed to archive '{src_path}': {e}")

