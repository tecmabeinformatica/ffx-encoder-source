from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .ffmpeg_tools import FfmpegTools, media_duration_seconds, test_encoder
from .media import ensure_dir, list_video_files
from .runner import run_with_percent


def _run_ffprobe_json(tools: FfmpegTools, file_path: Path, args: list[str]) -> dict:
    result = subprocess.run(
        [str(tools.ffprobe), "-v", "error", *args, "-of", "json", str(file_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def video_height(tools: FfmpegTools, file_path: Path) -> int:
    data = _run_ffprobe_json(
        tools,
        file_path,
        ["-select_streams", "v:0", "-show_entries", "stream=height"],
    )
    streams = data.get("streams", [])
    if not streams:
        return 0
    try:
        return int(streams[0].get("height", 0))
    except (TypeError, ValueError):
        return 0


def _codec_args(tools: FfmpegTools, codec: str, cq: str) -> list[str]:
    if codec == "h264":
        if test_encoder(tools, "h264_nvenc"):
            return ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", cq, "-b:v", "0"]
        if test_encoder(tools, "h264_qsv"):
            return ["-c:v", "h264_qsv", "-global_quality", cq]
        if test_encoder(tools, "h264_amf"):
            return ["-c:v", "h264_amf", "-cq", cq]
        return ["-c:v", "libx264", "-crf", cq, "-preset", "medium"]

    if codec == "av1":
        if test_encoder(tools, "av1_nvenc"):
            return ["-c:v", "av1_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", cq, "-b:v", "0"]
        if test_encoder(tools, "av1_qsv"):
            return ["-c:v", "av1_qsv", "-global_quality", cq]
        if test_encoder(tools, "av1_amf"):
            return ["-c:v", "av1_amf", "-cq", cq]
        if test_encoder(tools, "libsvtav1"):
            return ["-c:v", "libsvtav1", "-crf", cq, "-preset", "8"]
        return ["-c:v", "libaom-av1", "-crf", cq, "-b:v", "0", "-cpu-used", "6"]

    if test_encoder(tools, "hevc_nvenc"):
        return ["-c:v", "hevc_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", cq, "-b:v", "0"]
    if test_encoder(tools, "hevc_qsv"):
        return ["-c:v", "hevc_qsv", "-global_quality", cq]
    if test_encoder(tools, "hevc_amf"):
        return ["-c:v", "hevc_amf", "-cq", cq]
    return ["-c:v", "libx265", "-crf", cq, "-preset", "medium"]


def _audio_args(audio_mode: str) -> list[str]:
    if audio_mode == "copy":
        return ["-c:a", "copy"]
    return ["-c:a", "aac", "-b:a", "224k"]


def _map_args(tools: FfmpegTools, file_path: Path, container: str) -> tuple[list[str], list[str], list[str]]:
    if container != "mp4":
        return ["-map", "0"], ["-c:s", "copy"], []

    warnings: list[str] = []
    args = []
    data = _run_ffprobe_json(
        tools,
        file_path,
        ["-show_entries", "stream=index,codec_type,codec_name:stream_disposition=attached_pic"],
    )

    text_subtitles = {"subrip", "ass", "ssa", "webvtt", "mov_text"}
    for stream in data.get("streams", []):
        index = str(stream.get("index"))
        codec_type = stream.get("codec_type")
        codec_name = str(stream.get("codec_name", ""))
        attached_pic = int(stream.get("disposition", {}).get("attached_pic", 0))

        if codec_type == "video" and attached_pic == 1:
            warnings.append(f"[AVISO] Capa/anexo ignorado para MP4 em stream {index}")
            continue
        if codec_type == "attachment":
            warnings.append(f"[AVISO] Anexo ignorado para MP4 em stream {index}")
            continue
        if codec_type == "subtitle" and codec_name not in text_subtitles:
            warnings.append(f"[AVISO] Legenda {codec_name} ignorada para MP4 em stream {index}")
            continue

        args.extend(["-map", f"0:{index}"])

    return args, ["-c:s", "mov_text"], warnings


def convert_videos(work_dir: Path, tools: FfmpegTools, codec: str, container: str, audio_mode: str, cq: str) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Convertidos"
    ensure_dir(out_dir)
    extension = ".mp4" if container == "mp4" else ".mkv"

    video_args = _codec_args(tools, codec, cq)
    audio_args = _audio_args(audio_mode)

    for file_path in videos:
        out_file = out_dir / f"{file_path.stem}{extension}"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        selected_map_args, selected_subtitle_args, warnings = _map_args(tools, file_path, container)
        for warning in warnings:
            print(warning)

        duration = media_duration_seconds(tools, file_path)
        label = f"[CONVERTER] {file_path.name}"
        run_with_percent([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            *selected_map_args,
            *video_args,
            *audio_args,
            *selected_subtitle_args,
            out_file,
        ], label, duration)


def upscale_videos_1080p(work_dir: Path, tools: FfmpegTools, codec: str, container: str, audio_mode: str, cq: str) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Upscale"
    ensure_dir(out_dir)
    extension = ".mp4" if container == "mp4" else ".mkv"

    video_args = _codec_args(tools, codec, cq)
    audio_args = _audio_args(audio_mode)

    for file_path in videos:
        height = video_height(tools, file_path)
        if height <= 0:
            print(f"[PULADO] {file_path.name} - nao foi possivel detectar a resolucao")
            continue
        if height >= 1080:
            print(f"[PULADO] {file_path.name} - video ja possui {height}p")
            continue

        out_file = out_dir / f"{file_path.stem}{extension}"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        selected_map_args, selected_subtitle_args, warnings = _map_args(tools, file_path, container)
        for warning in warnings:
            print(warning)

        duration = media_duration_seconds(tools, file_path)
        label = f"[UPSCALE] {file_path.name} - {height}p para 1080p"
        run_with_percent([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            "-vf",
            "scale=-2:1080:flags=lanczos,format=yuv420p",
            *selected_map_args,
            *video_args,
            *audio_args,
            *selected_subtitle_args,
            out_file,
        ], label, duration)


def deinterlace_videos(
    work_dir: Path,
    tools: FfmpegTools,
    upscale_to_1080: bool,
    audio_mode: str,
    cq: str = "18",
) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Deinterlace"
    ensure_dir(out_dir)
    video_args = _codec_args(tools, "h265", cq)
    audio_args = _audio_args(audio_mode)

    for file_path in videos:
        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        height = video_height(tools, file_path)
        vf = "yadif=0:-1:0,format=yuv420p"
        label = f"[DEINTERLACE] {file_path.name}"
        if upscale_to_1080 and height > 0 and height < 1080:
            vf = "yadif=0:-1:0,scale=-2:1080:flags=lanczos,format=yuv420p"
            label = f"[DEINTERLACE] {file_path.name} - {height}p para 1080p"

        duration = media_duration_seconds(tools, file_path)
        run_with_percent([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            "-vf",
            vf,
            "-map",
            "0",
            *video_args,
            *audio_args,
            "-c:s",
            "copy",
            out_file,
        ], label, duration)


def filter_videos(
    work_dir: Path,
    tools: FfmpegTools,
    action_name: str,
    output_folder: str,
    video_filter: str,
    audio_mode: str = "copy",
    cq: str = "26",
) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / output_folder
    ensure_dir(out_dir)
    video_args = _codec_args(tools, "h265", cq)
    audio_args = _audio_args(audio_mode)

    for file_path in videos:
        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        duration = media_duration_seconds(tools, file_path)
        label = f"[{action_name}] {file_path.name}"
        run_with_percent([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            "-vf",
            video_filter,
            "-map",
            "0",
            *video_args,
            *audio_args,
            "-c:s",
            "copy",
            out_file,
        ], label, duration)
