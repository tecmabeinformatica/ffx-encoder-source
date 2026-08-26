from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig


@dataclass(frozen=True)
class FfmpegTools:
    ffmpeg: Path
    ffprobe: Path


def _find_executable(name: str, preferred_dirs: list[Path]) -> Path | None:
    for preferred_dir in preferred_dirs:
        preferred = preferred_dir / name
        if preferred.exists():
            return preferred

    found = shutil.which(name)
    if found:
        return Path(found)

    return None


def locate_ffmpeg(config: AppConfig) -> FfmpegTools:
    search_dirs = [config.local_ffmpeg_dir, config.bundled_ffmpeg_dir, config.ffmpeg_dir]
    ffmpeg = _find_executable("ffmpeg.exe", search_dirs)
    ffprobe = _find_executable("ffprobe.exe", search_dirs)

    if not ffmpeg or not ffprobe:
        raise FileNotFoundError(
            "FFmpeg/FFprobe nao encontrados. Coloque os arquivos em bin\\ "
            "ao lado do FFX Encoder, instale em C:\\FFmpeg\\bin ou adicione "
            "ffmpeg.exe e ffprobe.exe ao PATH do Windows."
        )

    return FfmpegTools(ffmpeg=ffmpeg, ffprobe=ffprobe)


def run_command(args: list[str | Path]) -> int:
    process = subprocess.run([str(arg) for arg in args])
    return process.returncode


def get_ffmpeg_version(tools: FfmpegTools) -> str:
    result = subprocess.run(
        [str(tools.ffmpeg), "-version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    return first_line.strip()


def detect_encoder_message(tools: FfmpegTools) -> str:
    if test_encoder(tools, "hevc_nvenc"):
        return "NVENC compativel (NVIDIA)"
    if test_encoder(tools, "hevc_qsv"):
        return "QSV compativel (Intel)"
    if test_encoder(tools, "hevc_amf"):
        return "AMF compativel (AMD)"
    return "CPU (libx265)"


def media_duration_seconds(tools: FfmpegTools, file_path: Path) -> float:
    result = subprocess.run(
        [
            str(tools.ffprobe),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def test_encoder(tools: FfmpegTools, encoder_name: str) -> bool:
    result = subprocess.run(
        [
            str(tools.ffmpeg),
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "nullsrc",
            "-frames:v",
            "1",
            "-c:v",
            encoder_name,
            "-f",
            "null",
            "-",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0
