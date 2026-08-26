from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .audio_subtitles import (
    _audio_streams,
    _find_external_subtitle,
    _find_forced_subtitle,
    _language,
    _map_pt_en_audio_pt_subtitles_ordered,
    _subtitle_streams,
)
from .config import AppConfig
from .covers import _cover_attach_args, _cover_replacement_map_args, _safe_name as _safe_cover_name
from .ffmpeg_tools import FfmpegTools
from .media import ensure_dir, list_video_files
from .metadata import GLOBAL_METADATA_KEYS, _movie_label, _safe_name, _stream_count
from .runner import run_with_spinner
from .tmdb import download_poster, search_movies


def _movie_query_from_file(file_path: Path) -> str:
    name = file_path.stem.replace(".", " ").replace("_", " ")
    return " ".join(name.split())


def _select_movie_interactive(initial_query: str, work_dir: Path) -> dict | None:
    query = initial_query
    while True:
        if not query:
            query = input("Digite o nome correto do filme ou pressione ENTER para cancelar: ").strip()
            if not query:
                return None

        results = search_movies(query, work_dir)
        if not results:
            print(f"[AVISO] Nao foi possivel localizar no TMDb por: {query}")
            query = input("Digite o nome correto do filme ou pressione ENTER para cancelar: ").strip()
            continue

        print("\nResultados encontrados:")
        for index, item in enumerate(results, start=1):
            print(f"{index} - {_movie_label(item)}")
        print("R - Digitar nova busca")
        print("C - Cancelar")

        choice = input("Escolha um resultado: ").strip().lower()
        if choice == "c":
            return None
        if choice == "r":
            query = input("Digite o nome correto do filme ou pressione ENTER para cancelar: ").strip()
            continue

        try:
            return results[int(choice) - 1]
        except (ValueError, IndexError):
            print("[AVISO] Escolha invalida.")


def _metadata_args_without_map(tools: FfmpegTools, file_path: Path, movie: dict) -> list[str]:
    title = movie.get("title") or file_path.stem
    year = (movie.get("release_date") or "")[:4]
    overview = movie.get("overview") or ""

    args = [
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

    args.extend([
        "-metadata",
        f"title={title}",
        "-metadata",
        f"description={overview}",
        "-metadata",
        f"synopsis={overview}",
        "-metadata",
        f"date={year}",
    ])
    return args


def _mux_external_subtitles_if_found(work_dir: Path, tools: FfmpegTools, source: Path, temp_dir: Path) -> Path:
    subtitle = _find_external_subtitle(work_dir, source.stem)
    forced = _find_forced_subtitle(work_dir, source.stem)
    if not subtitle:
        print("Etapa 1/4 - Nenhuma legenda externa encontrada. Seguindo...")
        return source

    print("Etapa 1/4 - Juntando legenda externa...")
    print(f"Legenda principal: {subtitle.name}")
    if forced:
        print(f"Legenda forced: {forced.name}")

    out_file = temp_dir / "01_legendas.mkv"
    existing_subtitle_count = len(_subtitle_streams(tools, source))
    args: list[str | Path] = [
        tools.ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-nostats",
        "-i",
        source,
        "-i",
        subtitle,
    ]
    if forced:
        args.extend(["-i", forced])

    args.extend([
        *_cover_replacement_map_args(tools, source),
        "-map",
        "1:0",
    ])
    if forced:
        args.extend(["-map", "2:0"])

    args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy"])
    args.extend([f"-metadata:s:s:{existing_subtitle_count}", "language=por"])
    args.extend([f"-disposition:s:{existing_subtitle_count}", "default"])

    if forced:
        forced_index = existing_subtitle_count + 1
        args.extend([f"-metadata:s:s:{forced_index}", "language=por"])
        args.extend([f"-disposition:s:{forced_index}", "forced"])

    args.append(out_file)
    return out_file if run_with_spinner(args, "[MODO INTELIGENTE] Legenda externa") == 0 else source


def _filter_pt_en_and_pt_subtitles(tools: FfmpegTools, source: Path, temp_dir: Path) -> Path | None:
    print("Etapa 2/4 - Mantendo PT+EN e legenda PT...")

    audio_streams = _audio_streams(tools, source)
    subtitle_streams = _subtitle_streams(tools, source)
    keep_subtitles = {str(stream.get("index")) for stream in subtitle_streams if _language(stream) == "por"}

    missing: list[str] = []
    if not any(_language(stream) == "por" for stream in audio_streams):
        missing.append("audio PT")
    if not any(_language(stream) == "eng" for stream in audio_streams):
        missing.append("audio EN")
    if not keep_subtitles:
        missing.append("legenda PT")

    if missing:
        print(f"[PULADO] faltando na rotina final: {', '.join(missing)}")
        return None

    out_file = temp_dir / "02_filtrado.mkv"
    args = [
        tools.ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-nostats",
        "-i",
        source,
        *_map_pt_en_audio_pt_subtitles_ordered(audio_streams, subtitle_streams),
        "-c",
        "copy",
        "-disposition:a",
        "0",
        "-disposition:a:0",
        "default",
        "-disposition:a:1",
        "0",
        out_file,
    ]
    return out_file if run_with_spinner(args, "[MODO INTELIGENTE] PT+EN/Legenda PT") == 0 else None


def _download_movie_cover(work_dir: Path, movie: dict) -> Path | None:
    poster_path = movie.get("poster_path")
    if not poster_path:
        print("[AVISO] Filme selecionado nao possui capa no TMDb.")
        return None

    cover_path = work_dir / "cover.jpg"
    download_poster(str(poster_path), cover_path)

    title = movie.get("title") or "Filme"
    year = (movie.get("release_date") or "")[:4]
    cache_dir = AppConfig().local_covers_dir / _safe_cover_name(title)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_name = f"{title} ({year})" if year else title
    cache_path = cache_dir / f"{_safe_cover_name(cache_name)}.jpg"
    cache_path.write_bytes(cover_path.read_bytes())
    print(f"[OK] Capa salva no cache: {cache_path}")
    return cover_path


def _write_final_file(work_dir: Path, tools: FfmpegTools, source: Path, movie: dict, cover_path: Path | None) -> Path | None:
    print("Etapa 4/4 - Limpando metadados antigos e gerando arquivo final com capa...")

    title = movie.get("title") or source.stem
    year = (movie.get("release_date") or "")[:4]
    out_dir = work_dir / "Saida" / "Modo_Inteligente"
    ensure_dir(out_dir)
    out_file = out_dir / f"{_safe_name(f'{title} {year}'.strip())}.mkv"

    if out_file.exists():
        print(f"[PULADO] arquivo de saida ja existe: {out_file.name}")
        return None

    args: list[str | Path] = [
        tools.ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-nostats",
        "-i",
        source,
        *_cover_replacement_map_args(tools, source),
        *_metadata_args_without_map(tools, source, movie),
    ]
    if cover_path and cover_path.exists():
        args.extend(_cover_attach_args(cover_path))
    args.append(out_file)

    return out_file if run_with_spinner(args, "[MODO INTELIGENTE] Arquivo final") == 0 else None


def run_movie_smart_mode(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    if len(videos) > 1:
        print("[PULADO] Esta rotina foi feita para um filme por pasta.")
        print("[AVISO] Deixe somente um video na pasta e tente novamente.")
        return

    source = videos[0]
    print(f"Arquivo base: {source.name}")
    temp_dir = Path(tempfile.mkdtemp(prefix="FFX_MovieReady_"))

    try:
        current = _mux_external_subtitles_if_found(work_dir, tools, source, temp_dir)
        filtered = _filter_pt_en_and_pt_subtitles(tools, current, temp_dir)
        if not filtered:
            return

        print("Etapa 3/4 - Buscando metadados corretos do filme...")
        movie = _select_movie_interactive(_movie_query_from_file(source), work_dir)
        if not movie:
            print("[PULADO] rotina cancelada.")
            return

        cover_path = _download_movie_cover(work_dir, movie)
        result = _write_final_file(work_dir, tools, filtered, movie, cover_path)
        if result:
            print(f"[OK] Filme final gerado: {result}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
