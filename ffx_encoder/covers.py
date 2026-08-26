from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from .ffmpeg_tools import FfmpegTools
from .media import ensure_dir, list_video_files
from .runner import run_with_spinner
from .config import AppConfig
from .tmdb import download_poster, search_multi, season_details


COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png")
CACHE_ROOTS = (AppConfig().local_covers_dir, AppConfig().fallback_covers_dir)


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


def find_local_cover(work_dir: Path) -> Path | None:
    for name in COVER_NAMES:
        candidate = work_dir / name
        if candidate.exists():
            return candidate
    return None


def _safe_name(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.rstrip(". ")


def _series_name_from_file(file_path: Path) -> str:
    name = file_path.stem
    match = re.search(r"\s+-\s+S\d{1,2}E\d{1,3}", name, flags=re.IGNORECASE)
    if match:
        return name[: match.start()].strip()

    if " - " in name:
        return name.split(" - ", 1)[0].strip()

    return re.sub(r"\s*\(?\b(19|20)\d{2}\b\)?\s*$", "", name).strip()


def _season_from_file(file_path: Path) -> int | None:
    match = re.search(r"S(\d{1,2})E\d{1,3}", file_path.stem, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _detect_cache_query(videos: list[Path]) -> tuple[str, int | None]:
    if not videos:
        return "", None

    query = _series_name_from_file(videos[0])
    seasons = {_season_from_file(video) for video in videos}
    seasons.discard(None)
    season = seasons.pop() if len(seasons) == 1 else None
    return query, season


def _cached_cover_path(query: str, season: int | None) -> tuple[Path | None, Path | None]:
    safe_query = _safe_name(query)
    if not safe_query:
        return None, None

    first_expected_dir: Path | None = None
    for cache_root in CACHE_ROOTS:
        title_dir = cache_root / safe_query
        if first_expected_dir is None:
            first_expected_dir = title_dir
        if not title_dir.exists():
            continue

        if season is not None:
            for extension in (".jpg", ".jpeg", ".png"):
                candidate = title_dir / f"Temporada {season}{extension}"
                if candidate.exists():
                    return candidate, first_expected_dir

        for name in ("Serie", safe_query):
            for extension in (".jpg", ".jpeg", ".png"):
                candidate = title_dir / f"{name}{extension}"
                if candidate.exists():
                    return candidate, first_expected_dir

    return None, first_expected_dir


def _is_cover_attachment(stream: dict) -> bool:
    tags = stream.get("tags", {})
    mimetype = str(tags.get("mimetype", "")).lower()
    filename = str(tags.get("filename", ""))

    if mimetype.startswith("image/"):
        return True

    return bool(re.match(r"(?i)^cover\.(jpg|jpeg|png|webp)$", filename))


def _cover_replacement_map_args(tools: FfmpegTools, file_path: Path) -> list[str]:
    map_args = ["-map", "0"]
    excluded_indexes: set[str] = set()

    attachment_data = _run_ffprobe_json(
        tools,
        file_path,
        ["-select_streams", "t", "-show_entries", "stream=index:stream_tags=mimetype,filename"],
    )
    for stream in attachment_data.get("streams", []):
        if _is_cover_attachment(stream):
            excluded_indexes.add(str(stream.get("index")))

    video_data = _run_ffprobe_json(
        tools,
        file_path,
        ["-select_streams", "v", "-show_entries", "stream=index:stream_disposition=attached_pic"],
    )
    for stream in video_data.get("streams", []):
        disposition = stream.get("disposition", {})
        if int(disposition.get("attached_pic", 0)) == 1:
            excluded_indexes.add(str(stream.get("index")))

    for index in sorted(excluded_indexes, key=lambda value: int(value) if value.isdigit() else 9999):
        if index and index != "None":
            map_args.extend(["-map", f"-0:{index}"])

    return map_args


def has_embedded_cover(tools: FfmpegTools, file_path: Path) -> bool:
    return len(_cover_replacement_map_args(tools, file_path)) > 2


def _cover_attach_args(cover_path: Path) -> list[str]:
    is_png = cover_path.suffix.lower() == ".png"
    mimetype = "image/png" if is_png else "image/jpeg"
    filename = "cover.png" if is_png else "cover.jpg"
    return [
        "-attach",
        str(cover_path),
        "-metadata:s:t",
        f"mimetype={mimetype}",
        "-metadata:s:t:0",
        f"filename={filename}",
    ]


def apply_local_cover(work_dir: Path, tools: FfmpegTools) -> None:
    cover_path = find_local_cover(work_dir)
    if not cover_path:
        print("[AVISO] arquivo cover.jpg, cover.jpeg ou cover.png nao encontrado.")
        return

    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Capas"
    ensure_dir(out_dir)

    print(f"Capa local encontrada: {cover_path.name}")

    for file_path in videos:
        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        label = f"[CAPAS] {file_path.name}"
        exit_code = run_with_spinner([
            str(tools.ffmpeg),
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            str(file_path),
            *_cover_replacement_map_args(tools, file_path),
            "-c",
            "copy",
            *_cover_attach_args(cover_path),
            str(out_file),
        ], label)
        if exit_code == 0:
            print(f"[OK] Salvo em: {out_file}")
        else:
            print(f"[ERRO] Falha ao aplicar capa em: {file_path.name}")


def apply_cover_from_cache(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    query, season = _detect_cache_query(videos)
    if not query:
        print("[AVISO] Nao foi possivel identificar um nome para busca no cache.")
        return

    print(f"Busca no cache por: {query}")
    if season is not None:
        print(f"Temporada detectada: {season}")

    cover_path, expected_dir = _cached_cover_path(query, season)
    if not cover_path:
        print("[AVISO] Nenhuma capa correspondente foi encontrada no cache.")
        if expected_dir:
            print(f"Pasta esperada: {expected_dir}")
        return

    print(f"Capa localizada no cache: {cover_path}")
    apply_cover_path_to_videos(work_dir, tools, cover_path, videos)


def _result_label(item: dict) -> str:
    media_type = "Serie" if item.get("media_type") == "tv" else "Filme"
    title = item.get("name") or item.get("title") or "Sem titulo"
    date = item.get("first_air_date") or item.get("release_date") or ""
    year = f" ({date[:4]})" if len(date) >= 4 else ""
    return f"{media_type} - {title}{year}"


def apply_cover_from_tmdb(work_dir: Path, tools: FfmpegTools, manual: bool = False) -> None:
    while True:
        videos = list_video_files(work_dir)
        if not videos:
            print("[AVISO] Nenhum video encontrado na pasta atual.")
            return

        query, season = _detect_cache_query(videos)
        if manual or not query:
            query = input("Digite o nome para busca: ").strip()
        if not query:
            print("[PULADO] busca cancelada")
            return

        results = search_multi(query, work_dir)
        if not results:
            print("[AVISO] Nenhum resultado encontrado.")
            return

        print("\nResultados encontrados:")
        for index, item in enumerate(results, start=1):
            print(f"{index} - {_result_label(item)}")
        print("R - Digitar nova busca")
        print("C - Cancelar")
        choice = input("Escolha um resultado: ").strip().lower()
        if choice == "c":
            return
        if choice == "r":
            manual = True
            continue
        try:
            selected = results[int(choice) - 1]
        except (ValueError, IndexError):
            print("[PULADO] escolha invalida")
            return

        poster_path = selected.get("poster_path")
        cache_folder = _safe_name(query)
        cache_file = "Serie"
        if selected.get("media_type") == "tv" and season is not None:
            try:
                details = season_details(int(selected["id"]), season, work_dir)
                if details.get("poster_path"):
                    poster_path = details["poster_path"]
                    cache_file = f"Temporada {season}"
            except Exception as exc:
                print(f"[AVISO] Falha ao buscar capa da temporada: {exc}")
        elif selected.get("media_type") == "movie":
            title = selected.get("title") or query
            year = (selected.get("release_date") or "")[:4]
            cache_folder = _safe_name(title)
            cache_file = f"{title} ({year})" if year else title

        temp_cover = work_dir / "cover.jpg"
        download_poster(str(poster_path), temp_cover)
        print(f"[OK] Capa baixada: {temp_cover.name}")
        try:
            os.startfile(temp_cover)
        except OSError:
            pass

        print("\nVerifique a imagem aberta e escolha:")
        print("1 - Aplicar capa")
        print("2 - Nova busca")
        print("3 - Cancelar")
        after_download = input("Escolha: ").strip()
        if after_download == "2":
            manual = True
            continue
        if after_download != "1":
            return

        local_cache = AppConfig().local_covers_dir / _safe_name(cache_folder) / f"{_safe_name(cache_file)}.jpg"
        local_cache.parent.mkdir(parents=True, exist_ok=True)
        local_cache.write_bytes(temp_cover.read_bytes())
        print(f"[OK] Capa salva no cache: {local_cache}")
        apply_cover_path_to_videos(work_dir, tools, temp_cover, videos)
        return


def apply_cover_path_to_videos(work_dir: Path, tools: FfmpegTools, cover_path: Path, videos: list[Path]) -> None:
    out_dir = work_dir / "Saida" / "Capas"
    ensure_dir(out_dir)

    for file_path in videos:
        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        label = f"[CAPAS] {file_path.name}"
        exit_code = run_with_spinner([
            str(tools.ffmpeg),
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            str(file_path),
            *_cover_replacement_map_args(tools, file_path),
            "-c",
            "copy",
            *_cover_attach_args(cover_path),
            str(out_file),
        ], label)
        if exit_code == 0:
            print(f"[OK] Salvo em: {out_file}")
        else:
            print(f"[ERRO] Falha ao aplicar capa em: {file_path.name}")


def remove_embedded_covers(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Capas" / "Sem_Capa"
    ensure_dir(out_dir)

    for file_path in videos:
        if not has_embedded_cover(tools, file_path):
            print(f"[PULADO] {file_path.name} - arquivo nao contem capa embutida")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        label = f"[REMOVER CAPA] {file_path.name}"
        exit_code = run_with_spinner([
            str(tools.ffmpeg),
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            str(file_path),
            *_cover_replacement_map_args(tools, file_path),
            "-c",
            "copy",
            str(out_file),
        ], label)
        if exit_code == 0:
            print(f"[OK] Salvo em: {out_file}")
        else:
            print(f"[ERRO] Falha ao remover capa de: {file_path.name}")
