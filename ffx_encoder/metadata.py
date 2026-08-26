from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .ffmpeg_tools import FfmpegTools
from .media import ensure_dir, list_video_files
from .runner import run_with_spinner
from .tmdb import download_poster, search_movies


GLOBAL_METADATA_KEYS = [
    "title",
    "comment",
    "description",
    "synopsis",
    "encoder",
    "artist",
    "album",
    "composer",
    "publisher",
    "genre",
    "date",
    "creation_time",
    "show",
    "network",
]


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


def _stream_count(tools: FfmpegTools, file_path: Path, selector: str) -> int:
    data = _run_ffprobe_json(
        tools,
        file_path,
        ["-select_streams", selector, "-show_entries", "stream=index"],
    )
    return len(data.get("streams", []))


def _metadata_report(tools: FfmpegTools, file_path: Path) -> tuple[list[str], list[str]]:
    data = _run_ffprobe_json(
        tools,
        file_path,
        ["-show_entries", "format_tags:stream=index,codec_type:stream_tags=title"],
    )
    global_items: list[str] = []
    stream_items: list[str] = []

    format_tags = data.get("format", {}).get("tags", {})
    for key in GLOBAL_METADATA_KEYS:
        value = format_tags.get(key)
        if value:
            global_items.append(f"{key}: {value}")

    for stream in data.get("streams", []):
        title = stream.get("tags", {}).get("title")
        if title:
            index = stream.get("index", "?")
            codec_type = stream.get("codec_type", "?")
            stream_items.append(f"stream {index} ({codec_type}) title: {title}")

    return global_items, stream_items


def _cleanup_args(tools: FfmpegTools, file_path: Path) -> list[str]:
    args = [
        "-map",
        "0",
        "-map_metadata",
        "0",
        "-map_chapters",
        "0",
        "-c",
        "copy",
    ]

    for key in GLOBAL_METADATA_KEYS:
        args.extend(["-metadata", f"{key}="])

    for selector in ("v", "a", "s"):
        count = _stream_count(tools, file_path, selector)
        for index in range(count):
            args.extend([f"-metadata:s:{selector}:{index}", "title="])

    return args


def clean_metadata(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Metadados" / "Limpos"
    ensure_dir(out_dir)

    for file_path in videos:
        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        print(f"\n[METADADOS] Limpando: {file_path.name}")
        global_items, stream_items = _metadata_report(tools, file_path)

        if global_items:
            print("Metadados globais encontrados:")
            for item in global_items:
                print(f"  - {item}")

        if stream_items:
            print("Titulos internos de streams encontrados:")
            for item in stream_items:
                print(f"  - {item}")

        if not global_items and not stream_items:
            print("Nenhum metadado textual relevante encontrado para limpeza.")
        else:
            print("Idiomas e flags das faixas serao preservados.")

        ffmpeg_args = [
            str(tools.ffmpeg),
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            str(file_path),
            *_cleanup_args(tools, file_path),
            str(out_file),
        ]
        exit_code = run_with_spinner(ffmpeg_args, f"[METADADOS] {file_path.name}")
        if exit_code == 0:
            print(f"[OK] Salvo em: {out_file}")
        else:
            print(f"[ERRO] Falha ao limpar metadados de: {file_path.name}")


def _safe_name(value: str) -> str:
    invalid = '<>:"/\\|?*'
    cleaned = "".join(ch for ch in value if ch not in invalid).strip()
    return " ".join(cleaned.split()).rstrip(". ")


def _movie_label(item: dict) -> str:
    title = item.get("title") or "Sem titulo"
    year = (item.get("release_date") or "")[:4]
    return f"Filme - {title} ({year})" if year else f"Filme - {title}"


def _movie_query_from_folder(work_dir: Path) -> str:
    videos = list_video_files(work_dir)
    if not videos:
        return ""
    name = videos[0].stem.replace(".", " ").replace("_", " ")
    return " ".join(name.split())


def insert_movie_metadata(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    query = input("Nome do filme (ENTER para detectar): ").strip() or _movie_query_from_folder(work_dir)
    results: list[dict] = []
    while True:
        if not query:
            print("[PULADO] busca cancelada")
            return

        results = search_movies(query, work_dir)
        if results:
            break

        print(f"[AVISO] Nao foi possivel localizar no TMDb por: {query}")
        query = input("Digite o nome correto do filme ou pressione ENTER para cancelar: ").strip()

    print("\nResultados encontrados:")
    for index, item in enumerate(results, start=1):
        print(f"{index} - {_movie_label(item)}")
    print("C - Cancelar")
    choice = input("Escolha um resultado: ").strip().lower()
    if choice == "c":
        return
    try:
        selected = results[int(choice) - 1]
    except (ValueError, IndexError):
        print("[PULADO] escolha invalida")
        return

    title = selected.get("title") or query
    year = (selected.get("release_date") or "")[:4]
    overview = selected.get("overview") or ""
    out_base = _safe_name(f"{title} {year}".strip())
    out_dir = work_dir / "Saida" / "Metadados" / "TMDb"
    ensure_dir(out_dir)

    cover_path = work_dir / "cover.jpg"
    if selected.get("poster_path"):
        download_poster(str(selected["poster_path"]), cover_path)

    for file_path in videos:
        out_file = out_dir / f"{out_base}.mkv"
        if len(videos) > 1:
            out_file = out_dir / f"{out_base} - {file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        args = [
            str(tools.ffmpeg),
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            str(file_path),
            *_cleanup_args(tools, file_path),
            "-metadata",
            f"title={title}",
            "-metadata",
            f"description={overview}",
            "-metadata",
            f"synopsis={overview}",
            "-metadata",
            f"date={year}",
        ]
        if cover_path.exists():
            args.extend([
                "-attach",
                str(cover_path),
                "-metadata:s:t",
                "mimetype=image/jpeg",
                "-metadata:s:t:0",
                "filename=cover.jpg",
            ])
        args.append(str(out_file))

        exit_code = run_with_spinner(args, f"[TMDB METADADOS] {file_path.name}")
        if exit_code == 0:
            print(f"[OK] Salvo em: {out_file}")
        else:
            print(f"[ERRO] Falha ao inserir metadados em: {file_path.name}")
