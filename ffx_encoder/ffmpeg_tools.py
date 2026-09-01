from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
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


def video_encoder_args(tools: FfmpegTools, codec: str, quality: str) -> list[str]:
    """Seleciona automaticamente o melhor encoder funcional para o codec pedido."""
    if codec == "copy":
        return ["-c:v", "copy"]

    encoder_names = {
        "h264": ("h264_nvenc", "h264_qsv", "h264_amf"),
        "hevc": ("hevc_nvenc", "hevc_qsv", "hevc_amf"),
        "av1": ("av1_nvenc", "av1_qsv", "av1_amf"),
    }
    nvenc, qsv, amf = encoder_names.get(codec, encoder_names["hevc"])

    if test_encoder(tools, nvenc):
        return ["-c:v", nvenc, "-preset", "p5", "-rc", "vbr", "-cq", quality, "-b:v", "0"]
    if test_encoder(tools, qsv):
        return ["-c:v", qsv, "-global_quality", quality]
    if test_encoder(tools, amf):
        # CQP e NV12 funcionam tambem em geracoes Radeon/AMF mais antigas.
        # QVBR/high_quality pode ser anunciado pelo FFmpeg, mas recusado em
        # tempo de execucao por placas ou drivers que nao oferecem o recurso.
        amf_args = [
            "-c:v", amf,
            "-pix_fmt", "nv12",
            "-quality", "quality",
            "-rc", "cqp",
            "-qp_i", quality,
            "-qp_p", quality,
        ]
        if codec in {"h264", "av1"}:
            amf_args.extend(["-qp_b", quality])
        return amf_args

    if codec == "h264":
        return ["-c:v", "libx264", "-preset", "medium", "-crf", quality]
    if codec == "av1":
        if test_encoder(tools, "libsvtav1"):
            return ["-c:v", "libsvtav1", "-crf", quality, "-preset", "8"]
        return ["-c:v", "libaom-av1", "-crf", quality, "-b:v", "0", "-cpu-used", "6"]
    return ["-c:v", "libx265", "-preset", "medium", "-crf", quality]


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


@lru_cache(maxsize=None)
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
