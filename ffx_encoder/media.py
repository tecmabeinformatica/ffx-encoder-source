from __future__ import annotations

from pathlib import Path


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".mpg",
    ".mpeg",
    ".ts",
    ".m2ts",
    ".webm",
    ".flv",
    ".wmv",
}


def list_video_files(work_dir: Path) -> list[Path]:
    if not work_dir.exists() or not work_dir.is_dir():
        return []

    return sorted(
        (
            item
            for item in work_dir.iterdir()
            if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
