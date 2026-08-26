from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from .ffmpeg_tools import FfmpegTools
from .media import ensure_dir, list_video_files
from .runner import run_with_spinner


AUDIO_EXTENSIONS = (".m4a", ".aac", ".mp3", ".ac3", ".eac3", ".dts", ".flac", ".opus", ".ogg", ".wav", ".mka")
SUBTITLE_EXTENSIONS = (".srt", ".ass", ".ssa")
FORCED_PATTERNS = (".forced", "_forced", ".forcado", "_forcado")


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


def _streams(tools: FfmpegTools, file_path: Path, stream_type: str | None = None) -> list[dict]:
    args = [
        "-show_entries",
        "stream=index,codec_type,codec_name,channels,bit_rate:stream_tags=language,title:stream_disposition=default,forced,hearing_impaired",
    ]
    if stream_type:
        args = ["-select_streams", stream_type, *args]
    return _run_ffprobe_json(tools, file_path, args).get("streams", [])


def _audio_streams(tools: FfmpegTools, file_path: Path) -> list[dict]:
    return _streams(tools, file_path, "a")


def _subtitle_streams(tools: FfmpegTools, file_path: Path) -> list[dict]:
    return _streams(tools, file_path, "s")


def _video_streams(tools: FfmpegTools, file_path: Path) -> list[dict]:
    return _streams(tools, file_path, "v")


def _language(stream: dict) -> str:
    return str(stream.get("tags", {}).get("language", "")).lower()


def _stream_title(stream: dict) -> str:
    return str(stream.get("tags", {}).get("title", "")).strip()


def _normalize_subtitle_language(stream: dict) -> str:
    language = _language(stream)
    title = _stream_title(stream).lower()

    mapping = {
        "por": "por",
        "pob": "por",
        "pt": "por",
        "pt-br": "por",
        "pt_br": "por",
        "eng": "en",
        "en": "en",
        "en-us": "en",
        "en_us": "en",
        "spa": "es",
        "es": "es",
    }
    if language in mapping:
        return mapping[language]

    title_checks = [
        ("por", ("port", "portugues", "portuguese", "brasil", "brazil", "pt-br", "pt_br")),
        ("en", ("english", "ingles", "eng")),
        ("es", ("spanish", "espanhol", "espanol", "latin", "latino")),
        ("ja", ("japanese", "japones", "japan")),
        ("fr", ("french", "frances")),
        ("de", ("german", "alemao", "deutsch")),
    ]
    for detected, words in title_checks:
        if any(word in title for word in words):
            return detected

    return "und"


def _audio_extension(codec_name: str) -> str:
    return {
        "aac": ".m4a",
        "mp3": ".mp3",
        "ac3": ".ac3",
        "eac3": ".eac3",
        "dts": ".dts",
        "flac": ".flac",
        "opus": ".opus",
        "vorbis": ".ogg",
        "pcm_s16le": ".wav",
    }.get(codec_name.lower(), ".mka")


def _subtitle_extension(codec_name: str) -> tuple[str, str]:
    codec = codec_name.lower()
    if codec == "subrip":
        return ".srt", "copy"
    if codec == "ass":
        return ".ass", "copy"
    if codec == "ssa":
        return ".ssa", "copy"
    if codec == "webvtt":
        return ".vtt", "copy"
    if codec == "mov_text":
        return ".srt", "srt"
    if codec == "hdmv_pgs_subtitle":
        return ".sup", "copy"
    if codec == "dvd_subtitle":
        return ".sub", "copy"
    return ".srt", "srt"


def _find_external_subtitle(work_dir: Path, base_name: str) -> Path | None:
    for extension in SUBTITLE_EXTENSIONS:
        candidate = work_dir / f"{base_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def _find_forced_subtitle(work_dir: Path, base_name: str) -> Path | None:
    for pattern in FORCED_PATTERNS:
        for extension in SUBTITLE_EXTENSIONS:
            candidate = work_dir / f"{base_name}{pattern}{extension}"
            if candidate.exists():
                return candidate
    return None


def _prepare_text_subtitle(subtitle: Path) -> tuple[Path, Path | None]:
    if subtitle.suffix.lower() not in {".srt", ".ass", ".ssa"}:
        return subtitle, None

    raw = subtitle.read_bytes()
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        return subtitle, None

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=subtitle.suffix, delete=False) as temp_file:
        temp_file.write(text)
        temp_path = Path(temp_file.name)

    return temp_path, temp_path


def _find_external_audio(work_dir: Path, base_name: str) -> Path | None:
    for extension in AUDIO_EXTENSIONS:
        candidate = work_dir / f"{base_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def _disposition_flag(stream: dict, name: str) -> bool:
    return int(stream.get("disposition", {}).get(name, 0) or 0) == 1


def _format_track_summary(entry: dict) -> str:
    flags = []
    if entry["default"]:
        flags.append("default")
    if entry["forced"]:
        flags.append("forced")
    if entry["hearing_impaired"]:
        flags.append("hearing_impaired")
    flags_text = f" - {', '.join(flags)}" if flags else ""
    title = f" - {entry['title']}" if entry["title"] else ""
    return f"{entry['label']} - {entry['language']} - {entry['codec']}{title}{flags_text}"


def _choose_track_language(current_language: str) -> str | None:
    print()
    print(f"Idioma atual: {current_language}")
    print("1 - por (Portugues)")
    print("2 - eng (Ingles)")
    print("3 - spa (Espanhol)")
    print("4 - und (Indefinido)")
    print("5 - Digitar codigo")
    print("6 - Cancelar")
    option = input("Escolha: ").strip() or "6"
    mapping = {"1": "por", "2": "eng", "3": "spa", "4": "und"}
    if option in mapping:
        return mapping[option]
    if option == "5":
        value = input("Codigo de idioma (ex: por, eng, spa): ").strip().lower()
        return value[:3] if value else None
    return None


def _build_organize_entries(tools: FfmpegTools, file_path: Path) -> list[dict]:
    entries = []
    for relative_index, stream in enumerate(_audio_streams(tools, file_path), start=1):
        entries.append({
            "type": "a",
            "relative": relative_index - 1,
            "label": f"Audio {relative_index}",
            "language": _language(stream) or "und",
            "codec": str(stream.get("codec_name", "desconhecido")),
            "title": _stream_title(stream),
            "default": _disposition_flag(stream, "default"),
            "forced": False,
            "hearing_impaired": _disposition_flag(stream, "hearing_impaired"),
        })

    for relative_index, stream in enumerate(_subtitle_streams(tools, file_path), start=1):
        entries.append({
            "type": "s",
            "relative": relative_index - 1,
            "label": f"Legenda {relative_index}",
            "language": _language(stream) or "und",
            "codec": str(stream.get("codec_name", "desconhecido")),
            "title": _stream_title(stream),
            "default": _disposition_flag(stream, "default"),
            "forced": _disposition_flag(stream, "forced"),
            "hearing_impaired": _disposition_flag(stream, "hearing_impaired"),
        })
    return entries


def organize_tracks(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / "Organizar_Faixas"
    ensure_dir(out_dir)

    for file_path in videos:
        entries = _build_organize_entries(tools, file_path)
        if not entries:
            print(f"[PULADO] {file_path.name} - sem audio ou legenda para organizar")
            continue

        changed = False
        while True:
            print()
            print("=========================================================")
            print(file_path.name)
            print("=========================================================")
            for number, entry in enumerate(entries, start=1):
                print(f"{number} - {_format_track_summary(entry)}")
            print("A - Aplicar alteracoes neste arquivo")
            print("P - Pular arquivo")
            print()
            choice = input("Escolha uma faixa para alterar: ").strip().lower()

            if choice == "p":
                print(f"[PULADO] {file_path.name}")
                break
            if choice == "a":
                if not changed:
                    print(f"[PULADO] {file_path.name} - nenhuma alteracao escolhida")
                    break
                out_file = out_dir / f"{file_path.stem}.mkv"
                if out_file.exists():
                    print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
                    break

                args: list[str | Path] = [
                    tools.ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-nostats",
                    "-i",
                    file_path,
                    "-map",
                    "0",
                    "-map_metadata",
                    "0",
                    "-map_chapters",
                    "0",
                    "-c",
                    "copy",
                    "-disposition:a",
                    "0",
                    "-disposition:s",
                    "0",
                ]

                for entry in entries:
                    args.extend([f"-metadata:s:{entry['type']}:{entry['relative']}", f"language={entry['language']}"])
                    flags = []
                    if entry["default"]:
                        flags.append("default")
                    if entry["forced"]:
                        flags.append("forced")
                    if entry["hearing_impaired"]:
                        flags.append("hearing_impaired")
                    if flags:
                        args.extend([f"-disposition:{entry['type']}:{entry['relative']}", "+".join(flags)])

                run_with_spinner([*args, out_file], f"[ORGANIZAR FAIXAS] {file_path.name}")
                break

            if not choice.isdigit() or not (1 <= int(choice) <= len(entries)):
                print("[AVISO] Opcao invalida.")
                continue

            selected = entries[int(choice) - 1]
            print()
            print(_format_track_summary(selected))
            print("1 - Alterar idioma")
            print("2 - Tornar default")
            print("3 - Remover default")
            if selected["type"] == "s":
                print("4 - Marcar forced")
                print("5 - Remover forced")
                print("6 - Marcar default + forced")
                print("7 - Voltar")
                action = input("Escolha: ").strip() or "7"
            else:
                print("4 - Voltar")
                action = input("Escolha: ").strip() or "4"

            if action == "1":
                language = _choose_track_language(selected["language"])
                if language:
                    selected["language"] = language
                    changed = True
            elif action == "2":
                for entry in entries:
                    if entry["type"] == selected["type"]:
                        entry["default"] = False
                selected["default"] = True
                changed = True
            elif action == "3":
                selected["default"] = False
                changed = True
            elif selected["type"] == "s" and action == "4":
                selected["forced"] = True
                changed = True
            elif selected["type"] == "s" and action == "5":
                selected["forced"] = False
                changed = True
            elif selected["type"] == "s" and action == "6":
                for entry in entries:
                    if entry["type"] == "s":
                        entry["default"] = False
                selected["default"] = True
                selected["forced"] = True
                changed = True


def _build_editor_entries(tools: FfmpegTools, file_path: Path) -> list[dict]:
    counters = {"v": 0, "a": 0, "s": 0, "t": 0, "d": 0}
    labels = {"v": "Video", "a": "Audio", "s": "Legenda", "t": "Anexo", "d": "Dados"}
    entries = []

    for stream in _streams(tools, file_path):
        codec_type = str(stream.get("codec_type", "data")).lower()
        stream_type = {
            "video": "v",
            "audio": "a",
            "subtitle": "s",
            "attachment": "t",
            "data": "d",
        }.get(codec_type, "d")
        counters[stream_type] += 1
        tags = stream.get("tags", {})
        filename = str(tags.get("filename") or tags.get("FILENAME") or "").strip()
        mimetype = str(tags.get("mimetype") or tags.get("MIMETYPE") or "").strip()
        title = _stream_title(stream) or filename or mimetype
        entries.append({
            "keep": True,
            "source_index": int(stream.get("index", 0)),
            "type": stream_type,
            "relative": counters[stream_type] - 1,
            "label": f"{labels[stream_type]} {counters[stream_type]}",
            "language": _language(stream) or "und",
            "codec": str(stream.get("codec_name", "desconhecido")),
            "title": title,
            "default": _disposition_flag(stream, "default"),
            "forced": _disposition_flag(stream, "forced") if stream_type == "s" else False,
            "hearing_impaired": _disposition_flag(stream, "hearing_impaired"),
        })
    return entries


def _format_editor_entry(entry: dict) -> str:
    status = "manter" if entry["keep"] else "remover"
    flags = []
    if entry["type"] in {"a", "s"} and entry["default"]:
        flags.append("default")
    if entry["type"] == "s" and entry["forced"]:
        flags.append("forced")
    if entry["type"] in {"a", "s"} and entry["hearing_impaired"]:
        flags.append("hearing_impaired")
    flags_text = f" - {', '.join(flags)}" if flags else ""
    language = f" - {entry['language']}" if entry["type"] in {"a", "s"} else ""
    title = f" - {entry['title']}" if entry["title"] else ""
    return f"{entry['label']} - {entry['codec']}{language}{title}{flags_text} - {status}"


def _refresh_editor_labels(entries: list[dict]) -> None:
    counters = {"v": 0, "a": 0, "s": 0, "t": 0, "d": 0}
    labels = {"v": "Video", "a": "Audio", "s": "Legenda", "t": "Anexo", "d": "Dados"}
    for entry in entries:
        counters[entry["type"]] += 1
        entry["relative"] = counters[entry["type"]] - 1
        entry["label"] = f"{labels[entry['type']]} {counters[entry['type']]}"


def _move_editor_entry(entries: list[dict], selected: dict, direction: int) -> bool:
    same_type_positions = [index for index, entry in enumerate(entries) if entry["type"] == selected["type"]]
    current_position = entries.index(selected)
    current_type_position = same_type_positions.index(current_position)
    new_type_position = current_type_position + direction

    if new_type_position < 0 or new_type_position >= len(same_type_positions):
        return False

    target_position = same_type_positions[new_type_position]
    entries[current_position], entries[target_position] = entries[target_position], entries[current_position]
    _refresh_editor_labels(entries)
    return True


def _parse_editor_selection(raw: str, total: int) -> list[int] | None:
    selected: set[int] = set()
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start_text, _, end_text = part.partition("-")
            if not start_text.isdigit() or not end_text.isdigit():
                return None
            start = int(start_text)
            end = int(end_text)
            if start > end:
                start, end = end, start
            if start < 1 or end > total:
                return None
            selected.update(range(start, end + 1))
        else:
            if not part.isdigit():
                return None
            number = int(part)
            if number < 1 or number > total:
                return None
            selected.add(number)
    return sorted(selected)


def _is_image_video(entry: dict, video_position: int) -> bool:
    if entry["type"] != "v" or video_position == 1:
        return False
    codec = entry["codec"].lower()
    title = entry["title"].lower()
    image_codecs = {"mjpeg", "png", "apng", "webp", "bmp", "gif", "jpeg2000"}
    return codec in image_codecs or "cover" in title or "image/" in title


def _confirm_editor_apply(file_path: Path, out_file: Path, entries: list[dict]) -> bool | None:
    kept = [entry for entry in entries if entry["keep"]]
    removed = [entry for entry in entries if not entry["keep"]]

    while True:
        print()
        print("=========================================================")
        print("  RESUMO ANTES DE APLICAR")
        print("=========================================================")
        print(file_path.name)
        print()
        print("SERA MANTIDO:")
        for entry in kept:
            print(f"- {_format_editor_entry(entry).replace(' - manter', '')}")
        print()
        print("SERA REMOVIDO:")
        if removed:
            for entry in removed:
                print(f"- {_format_editor_entry(entry).replace(' - remover', '')}")
        else:
            print("- Nada")
        print()
        print(f"Saida: {out_file}")
        print()
        print("1 - Confirmar e aplicar")
        print("2 - Voltar para editar")
        print("3 - Cancelar arquivo")
        option = input("Escolha: ").strip() or "2"
        if option == "1":
            return True
        if option == "2":
            return None
        if option == "3":
            return False
        print("[AVISO] Opcao invalida.")


def edit_tracks_manual(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / "Editor_Faixas"
    ensure_dir(out_dir)

    for file_path in videos:
        entries = _build_editor_entries(tools, file_path)
        if not entries:
            print(f"[PULADO] {file_path.name} - nenhuma faixa encontrada")
            continue

        changed = False
        while True:
            print()
            print("=========================================================")
            print(file_path.name)
            print("=========================================================")
            for number, entry in enumerate(entries, start=1):
                print(f"{number} - {_format_editor_entry(entry)}")
            print("A - Aplicar neste arquivo")
            print("P - Pular arquivo")
            print("M - Marcar tudo para manter")
            print("S - Remover todas as legendas")
            print("C - Remover anexos/capas")
            print("I - Remover imagens em faixas de video")
            print("Exemplos: 4,5,6 ou 4-20 alterna manter/remover em lote")
            print()
            choice = input("Escolha uma faixa para editar: ").strip().lower()

            if choice == "p":
                print(f"[PULADO] {file_path.name}")
                break
            if choice == "m":
                for entry in entries:
                    entry["keep"] = True
                changed = True
                continue
            if choice == "s":
                for entry in entries:
                    if entry["type"] == "s":
                        entry["keep"] = False
                changed = True
                continue
            if choice == "c":
                for entry in entries:
                    if entry["type"] == "t":
                        entry["keep"] = False
                changed = True
                continue
            if choice == "i":
                video_position = 0
                removed_any = False
                for entry in entries:
                    if entry["type"] == "v":
                        video_position += 1
                        if _is_image_video(entry, video_position):
                            entry["keep"] = False
                            removed_any = True
                if removed_any:
                    changed = True
                else:
                    print("[AVISO] Nenhuma imagem em faixa de video foi encontrada.")
                continue
            if choice == "a":
                kept_entries = [entry for entry in entries if entry["keep"]]
                if not kept_entries:
                    print("[AVISO] Nenhuma faixa marcada para manter.")
                    continue
                if not any(entry["type"] == "v" for entry in kept_entries):
                    print("[AVISO] Pelo menos uma faixa de video precisa ser mantida.")
                    continue
                if not changed:
                    print(f"[PULADO] {file_path.name} - nenhuma alteracao escolhida")
                    break

                out_file = out_dir / f"{file_path.stem}.mkv"
                if out_file.exists():
                    print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
                    break

                confirmation = _confirm_editor_apply(file_path, out_file, entries)
                if confirmation is None:
                    continue
                if confirmation is False:
                    print(f"[PULADO] {file_path.name}")
                    break

                args: list[str | Path] = [
                    tools.ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-nostats",
                    "-i",
                    file_path,
                ]
                for entry in kept_entries:
                    args.extend(["-map", f"0:{entry['source_index']}"])
                args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", "-disposition:a", "0", "-disposition:s", "0"])

                output_relative = {"a": 0, "s": 0}
                for entry in kept_entries:
                    if entry["type"] not in {"a", "s"}:
                        continue
                    relative = output_relative[entry["type"]]
                    output_relative[entry["type"]] += 1
                    args.extend([f"-metadata:s:{entry['type']}:{relative}", f"language={entry['language']}"])
                    flags = []
                    if entry["default"]:
                        flags.append("default")
                    if entry["forced"]:
                        flags.append("forced")
                    if entry["hearing_impaired"]:
                        flags.append("hearing_impaired")
                    if flags:
                        args.extend([f"-disposition:{entry['type']}:{relative}", "+".join(flags)])

                run_with_spinner([*args, out_file], f"[EDITOR FAIXAS] {file_path.name}")
                break

            if "," in choice or "-" in choice:
                selected_numbers = _parse_editor_selection(choice, len(entries))
                if not selected_numbers:
                    print("[AVISO] Selecao invalida.")
                    continue
                for number in selected_numbers:
                    entries[number - 1]["keep"] = not entries[number - 1]["keep"]
                changed = True
                continue

            if not choice.isdigit() or not (1 <= int(choice) <= len(entries)):
                print("[AVISO] Opcao invalida.")
                continue

            selected = entries[int(choice) - 1]
            print()
            print(_format_editor_entry(selected))
            print("1 - Alternar manter/remover")
            if selected["type"] in {"a", "s"}:
                print("2 - Alterar idioma")
                print("3 - Tornar default")
                print("4 - Remover default")
                if selected["type"] == "s":
                    print("5 - Marcar forced")
                    print("6 - Remover forced")
                    print("7 - Marcar default + forced")
                    print("8 - Mover para cima")
                    print("9 - Mover para baixo")
                    print("10 - Voltar")
                    action = input("Escolha: ").strip() or "10"
                else:
                    print("5 - Mover para cima")
                    print("6 - Mover para baixo")
                    print("7 - Voltar")
                    action = input("Escolha: ").strip() or "7"
            else:
                print("2 - Mover para cima")
                print("3 - Mover para baixo")
                print("4 - Voltar")
                action = input("Escolha: ").strip() or "4"

            if action == "1":
                selected["keep"] = not selected["keep"]
                changed = True
            elif selected["type"] in {"a", "s"} and action == "2":
                language = _choose_track_language(selected["language"])
                if language:
                    selected["language"] = language
                    changed = True
            elif selected["type"] in {"a", "s"} and action == "3":
                for entry in entries:
                    if entry["type"] == selected["type"]:
                        entry["default"] = False
                selected["default"] = True
                changed = True
            elif selected["type"] in {"a", "s"} and action == "4":
                selected["default"] = False
                changed = True
            elif selected["type"] == "s" and action == "5":
                selected["forced"] = True
                changed = True
            elif selected["type"] == "s" and action == "6":
                selected["forced"] = False
                changed = True
            elif selected["type"] == "s" and action == "7":
                for entry in entries:
                    if entry["type"] == "s":
                        entry["default"] = False
                selected["default"] = True
                selected["forced"] = True
                changed = True
            elif selected["type"] == "a" and action == "5":
                if _move_editor_entry(entries, selected, -1):
                    changed = True
                else:
                    print("[AVISO] Esta faixa ja esta no topo do seu tipo.")
            elif selected["type"] == "a" and action == "6":
                if _move_editor_entry(entries, selected, 1):
                    changed = True
                else:
                    print("[AVISO] Esta faixa ja esta no fim do seu tipo.")
            elif selected["type"] == "s" and action == "8":
                if _move_editor_entry(entries, selected, -1):
                    changed = True
                else:
                    print("[AVISO] Esta faixa ja esta no topo do seu tipo.")
            elif selected["type"] == "s" and action == "9":
                if _move_editor_entry(entries, selected, 1):
                    changed = True
                else:
                    print("[AVISO] Esta faixa ja esta no fim do seu tipo.")
            elif selected["type"] not in {"a", "s"} and action == "2":
                if _move_editor_entry(entries, selected, -1):
                    changed = True
                else:
                    print("[AVISO] Esta faixa ja esta no topo do seu tipo.")
            elif selected["type"] not in {"a", "s"} and action == "3":
                if _move_editor_entry(entries, selected, 1):
                    changed = True
                else:
                    print("[AVISO] Esta faixa ja esta no fim do seu tipo.")


def _map_keep_audio_subtitles(
    tools: FfmpegTools,
    file_path: Path,
    keep_audio_indexes: set[str],
    keep_subtitle_indexes: set[str],
) -> list[str]:
    map_args = ["-map", "0"]

    for stream in _audio_streams(tools, file_path):
        index = str(stream.get("index"))
        if index not in keep_audio_indexes:
            map_args.extend(["-map", f"-0:{index}"])

    for stream in _subtitle_streams(tools, file_path):
        index = str(stream.get("index"))
        if index not in keep_subtitle_indexes:
            map_args.extend(["-map", f"-0:{index}"])

    return map_args


def _map_pt_en_audio_pt_subtitles_ordered(
    audio_streams: list[dict],
    subtitle_streams: list[dict],
) -> list[str]:
    map_args = ["-map", "0:v?"]

    portuguese_audio = [stream for stream in audio_streams if _language(stream) == "por"]
    english_audio = [stream for stream in audio_streams if _language(stream) == "eng"]
    portuguese_subtitles = [stream for stream in subtitle_streams if _language(stream) == "por"]

    for stream in [*portuguese_audio, *english_audio]:
        map_args.extend(["-map", f"0:{stream.get('index')}"])

    for stream in portuguese_subtitles:
        map_args.extend(["-map", f"0:{stream.get('index')}"])

    # Preserve attachments such as MKV covers when present.
    map_args.extend(["-map", "0:t?"])
    return map_args


def keep_only_audio_track(work_dir: Path, tools: FfmpegTools, track_number: int) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / f"Faixa_{track_number}"
    ensure_dir(out_dir)

    for file_path in videos:
        audio_streams = _audio_streams(tools, file_path)
        selected_position = track_number - 1
        if len(audio_streams) <= selected_position:
            print(f"[PULADO] {file_path.name} - arquivo nao contem faixa {track_number} de audio")
            continue

        selected_index = str(audio_streams[selected_position].get("index"))
        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        map_args = _map_keep_audio_subtitles(tools, file_path, {selected_index}, set())

        label = f"[AUDIO {track_number}] {file_path.name}"
        exit_code = run_with_spinner([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            *map_args,
            "-c",
            "copy",
            out_file,
        ], label)


def keep_portuguese_audio(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / "PT"
    ensure_dir(out_dir)

    for file_path in videos:
        keep_audio = {str(stream.get("index")) for stream in _audio_streams(tools, file_path) if _language(stream) == "por"}
        if not keep_audio:
            print(f"[PULADO] {file_path.name} - arquivo nao contem audio em portugues")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        run_with_spinner([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            *_map_keep_audio_subtitles(tools, file_path, keep_audio, set()),
            "-c",
            "copy",
            out_file,
        ], f"[AUDIO PT] {file_path.name}")


def keep_pt_en_audio_with_pt_subtitles(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / "PT_EN_Legenda_PT"
    ensure_dir(out_dir)

    for file_path in videos:
        audio_streams = _audio_streams(tools, file_path)
        subtitle_streams = _subtitle_streams(tools, file_path)
        keep_subtitles = {str(stream.get("index")) for stream in subtitle_streams if _language(stream) == "por"}

        missing: list[str] = []
        if not any(_language(stream) == "por" for stream in audio_streams):
            missing.append("audio PT")
        if not any(_language(stream) == "eng" for stream in audio_streams):
            missing.append("audio EN")
        if not keep_subtitles:
            missing.append("legenda PT")
        if missing:
            print(f"[PULADO] {file_path.name} - faltando: {', '.join(missing)}")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        run_with_spinner([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
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
        ], f"[PT+EN] {file_path.name}")


def _select_audio_streams(tools: FfmpegTools, file_path: Path, selector: str) -> list[dict]:
    audio_streams = _audio_streams(tools, file_path)
    if selector == "audio1":
        return audio_streams[:1]
    if selector == "audio2":
        return audio_streams[1:2]
    if selector == "pt":
        return [stream for stream in audio_streams if _language(stream) == "por"]
    if selector == "all":
        return audio_streams
    return audio_streams[:1]


def extract_audio(work_dir: Path, tools: FfmpegTools, selector: str, audio_format: str) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / "Extraido"
    ensure_dir(out_dir)

    for file_path in videos:
        selected_streams = _select_audio_streams(tools, file_path, selector)
        if not selected_streams:
            reason = "arquivo nao contem audio"
            if selector == "audio2":
                reason = "arquivo nao contem faixa 2 de audio"
            elif selector == "pt":
                reason = "arquivo nao contem audio em portugues"
            print(f"[PULADO] {file_path.name} - {reason}")
            continue

        for counter, stream in enumerate(selected_streams, start=1):
            suffix = {
                "audio1": "audio1",
                "audio2": "audio2",
                "pt": "pt" if len(selected_streams) == 1 else f"pt_{counter}",
                "all": f"audio{counter}",
            }.get(selector, f"audio{counter}")

            stream_index = str(stream.get("index"))
            codec_name = str(stream.get("codec_name", ""))
            if audio_format == "aac":
                out_file = out_dir / f"{file_path.stem}_{suffix}.m4a"
                codec_args = ["-c:a", "aac", "-b:a", "224k"]
            elif audio_format == "mp3":
                out_file = out_dir / f"{file_path.stem}_{suffix}.mp3"
                codec_args = ["-c:a", "libmp3lame", "-b:a", "320k"]
            else:
                out_file = out_dir / f"{file_path.stem}_{suffix}{_audio_extension(codec_name)}"
                codec_args = ["-c:a", "copy"]

            if out_file.exists():
                print(f"[PULADO] {out_file.name} - arquivo de saida ja existe")
                continue

            label = f"[EXTRAIR AUDIO] {file_path.name}"
            exit_code = run_with_spinner([
                tools.ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-nostats",
                "-i",
                file_path,
                "-map",
                f"0:{stream_index}",
                "-vn",
                *codec_args,
                out_file,
            ], label)


def _print_subtitle_streams(streams: list[dict]) -> None:
    if not streams:
        print("Nenhuma legenda encontrada.")
        return

    print("Legendas encontradas:")
    print()
    for stream in streams:
        index = stream.get("index")
        codec = stream.get("codec_name", "?")
        language = _normalize_subtitle_language(stream)
        title = _stream_title(stream)
        title_text = f" - {title}" if title else ""
        print(f"{index} - {codec} - {language}{title_text}")


def _subtitle_summary(stream: dict) -> str:
    index = stream.get("index")
    codec = stream.get("codec_name", "?")
    language = _normalize_subtitle_language(stream)
    title = _stream_title(stream)
    title_text = f" - {title}" if title else ""
    return f"stream {index} - {codec} - {language}{title_text}"


def _stream_flags(stream: dict) -> list[str]:
    disposition = stream.get("disposition", {})
    flags: list[str] = []
    if int(disposition.get("default", 0)) == 1:
        flags.append("default")
    if int(disposition.get("forced", 0)) == 1:
        flags.append("forced")
    if int(disposition.get("hearing_impaired", 0)) == 1:
        flags.append("hearing_impaired")
    return flags


def _audio_layout(channels: int | str | None) -> str:
    try:
        channel_count = int(channels or 0)
    except (TypeError, ValueError):
        channel_count = 0
    return {
        1: "1.0",
        2: "2.0",
        6: "5.1",
        8: "7.1",
    }.get(channel_count, f"{channel_count}ch" if channel_count else "")


def _bitrate_kbps(value: int | str | None) -> str:
    try:
        bitrate = int(value or 0)
    except (TypeError, ValueError):
        bitrate = 0
    return f"{round(bitrate / 1000)}kbps" if bitrate > 0 else ""


def generate_tracks_report(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Relatorios"
    ensure_dir(out_dir)
    out_file = out_dir / "relatorio_faixas.txt"

    lines: list[str] = [
        "RELATORIO DE FAIXAS",
        f"Pasta: {work_dir}",
        "",
    ]

    for file_path in videos:
        lines.extend([
            "=========================================================",
            file_path.name,
            "=========================================================",
        ])

        data = _run_ffprobe_json(
            tools,
            file_path,
            [
                "-show_entries",
                "stream=index,codec_type,codec_name,channels,bit_rate:stream_tags=language,title:stream_disposition=default,forced,hearing_impaired",
            ],
        )
        streams = data.get("streams", [])
        audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]
        subtitle_streams = [stream for stream in streams if stream.get("codec_type") == "subtitle"]

        if not audio_streams:
            lines.append("audio: nenhum")

        for counter, stream in enumerate(audio_streams, start=1):
            language = _language(stream) or "und"
            codec = stream.get("codec_name", "?")
            layout = _audio_layout(stream.get("channels"))
            bitrate = _bitrate_kbps(stream.get("bit_rate"))
            flags = " ".join(_stream_flags(stream))
            parts = [f"audio{counter}", f"({language})", str(codec), layout, bitrate, flags]
            lines.append("  ".join(part for part in parts if part).strip())

        if not subtitle_streams:
            lines.append("legenda: nenhuma")

        for counter, stream in enumerate(subtitle_streams, start=1):
            language = _normalize_subtitle_language(stream)
            codec = stream.get("codec_name", "?")
            flags = " ".join(_stream_flags(stream))
            parts = [f"legenda{counter}", f"({language})", str(codec), flags]
            lines.append("  ".join(part for part in parts if part).strip())

        lines.append("")

    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Relatorio salvo em: {out_file}")


def _parse_stream_indexes(raw: str, valid_indexes: set[str]) -> list[str]:
    selected: list[str] = []
    for item in raw.replace(",", " ").split():
        if item in valid_indexes and item not in selected:
            selected.append(item)
    return selected


def extract_subtitles(work_dir: Path, tools: FfmpegTools, extract_all: bool = False) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Legendas" / "Extraidas"
    ensure_dir(out_dir)

    for file_path in videos:
        streams = _subtitle_streams(tools, file_path)
        if not streams:
            print(f"[PULADO] {file_path.name} - arquivo nao contem legendas")
            continue

        selected_indexes = [str(stream.get("index")) for stream in streams]
        if not extract_all:
            print()
            print(f"Arquivo: {file_path.name}")
            print()
            _print_subtitle_streams(streams)
            print()
            print("Aperte ENTER para nao extrair nada deste arquivo.")
            print("Para extrair, digite o numero da legenda. Exemplo: 4")
            print("Para extrair mais de uma, digite separado por espaco. Exemplo: 4 5")
            raw = input("Extrair legenda: ").strip()
            if not raw:
                print("[PULADO] nenhuma legenda extraida deste arquivo")
                continue
            selected_indexes = _parse_stream_indexes(raw, set(selected_indexes))
            if not selected_indexes:
                print("[AVISO] Nenhuma legenda valida selecionada.")
                continue

        stream_by_index = {str(stream.get("index")): stream for stream in streams}
        for stream_index in selected_indexes:
            stream = stream_by_index.get(stream_index)
            if not stream:
                print(f"[AVISO] Legenda {stream_index} nao encontrada em: {file_path.name}")
                continue

            codec_name = str(stream.get("codec_name", ""))
            language = _normalize_subtitle_language(stream)
            extension, codec_output = _subtitle_extension(codec_name)
            out_file = out_dir / f"{file_path.stem} ({language}) [{stream_index}]{extension}"
            if out_file.exists():
                print(f"[PULADO] {out_file.name} - arquivo de saida ja existe")
                continue

            codec_args = ["-c", "copy"] if codec_output == "copy" else ["-c:s", codec_output]
            run_with_spinner([
                tools.ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-nostats",
                "-i",
                file_path,
                "-map",
                f"0:{stream_index}",
                *codec_args,
                out_file,
            ], f"[EXTRAIR LEGENDA] {file_path.name} [{stream_index}]")


def remove_subtitles(work_dir: Path, tools: FfmpegTools) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Legendas" / "Removidas"
    ensure_dir(out_dir)

    for file_path in videos:
        streams = _subtitle_streams(tools, file_path)
        if not streams:
            print(f"[PULADO] {file_path.name} - arquivo nao contem legendas")
            continue

        print()
        print(f"Arquivo: {file_path.name}")
        print()
        _print_subtitle_streams(streams)
        print()
        print("Aperte ENTER para nao remover nada deste arquivo.")
        print("Para remover, digite o numero da legenda. Exemplo: 3")
        print("Para remover mais de uma, digite separado por espaco. Exemplo: 3 5")
        raw = input("Remover legenda: ").strip()
        if not raw:
            print("[PULADO] nenhuma legenda removida deste arquivo")
            continue

        selected_indexes = _parse_stream_indexes(raw, {str(stream.get("index")) for stream in streams})
        if not selected_indexes:
            print("[AVISO] Nenhuma legenda valida selecionada.")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        map_args = ["-map", "0"]
        for stream_index in selected_indexes:
            map_args.extend(["-map", f"-0:{stream_index}"])

        run_with_spinner([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            *map_args,
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c",
            "copy",
            out_file,
        ], f"[REMOVER LEGENDA] {file_path.name}")


def remove_subtitles_by_position(work_dir: Path, tools: FfmpegTools, position: int) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    if position <= 0:
        print("[AVISO] Posicao invalida.")
        return

    planned: list[tuple[Path, dict | None]] = []
    print("Resumo do lote:")
    print()
    for file_path in videos:
        streams = _subtitle_streams(tools, file_path)
        selected = streams[position - 1] if len(streams) >= position else None
        planned.append((file_path, selected))
        if selected:
            print(f"{file_path.name} -> remover legenda {position}: {_subtitle_summary(selected)}")
        else:
            print(f"{file_path.name} -> [PULADO] nao contem legenda {position}")

    if not any(selected for _, selected in planned):
        print()
        print("[AVISO] Nenhum arquivo contem essa posicao de legenda.")
        return

    print()
    print("Confirmar remocao no lote?")
    print("1 - Sim")
    print("2 - Nao")
    confirm = input("Escolha: ").strip()
    if confirm != "1":
        print("[PULADO] remocao em lote cancelada")
        return

    out_dir = work_dir / "Saida" / "Legendas" / "Removidas"
    ensure_dir(out_dir)

    for file_path, selected in planned:
        if not selected:
            print(f"[PULADO] {file_path.name} - nao contem legenda {position}")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        stream_index = str(selected.get("index"))
        run_with_spinner([
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            "-map",
            "0",
            "-map",
            f"-0:{stream_index}",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c",
            "copy",
            out_file,
        ], f"[REMOVER LEGENDA LOTE] {file_path.name}")


def mux_external_subtitles(work_dir: Path, tools: FfmpegTools, language: str = "por", delay_ms: int = 0) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Legendas" / "Mux_Externa"
    ensure_dir(out_dir)
    offset = f"{delay_ms / 1000:.3f}"

    for file_path in videos:
        subtitle = _find_external_subtitle(work_dir, file_path.stem)
        forced = _find_forced_subtitle(work_dir, file_path.stem)
        if not subtitle:
            print(f"[PULADO] {file_path.name} - legenda externa nao encontrada")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        prepared_subtitle, subtitle_temp = _prepare_text_subtitle(subtitle)
        prepared_forced, forced_temp = _prepare_text_subtitle(forced) if forced else (None, None)

        try:
            existing_subtitle_count = len(_subtitle_streams(tools, file_path))
            input_args: list[str | Path] = [tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", file_path]
            input_args.extend(["-itsoffset", offset, "-i", prepared_subtitle])
            if prepared_forced:
                input_args.extend(["-itsoffset", offset, "-i", prepared_forced])

            output_args: list[str | Path] = ["-map", "0:v:0?", "-map", "0:a?", "-map", "0:s?", "-map", "1:0"]
            if prepared_forced:
                output_args.extend(["-map", "2:0"])

            for extra_video_index in range(1, len(_video_streams(tools, file_path))):
                output_args.extend(["-map", f"0:v:{extra_video_index}?"])
            output_args.extend(["-map", "0:t?", "-map", "0:d?"])

            output_args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", "-disposition:s", "0"])

            new_full_index = existing_subtitle_count
            output_args.extend([f"-metadata:s:s:{new_full_index}", f"language={language}"])
            output_args.extend([f"-disposition:s:{new_full_index}", "default"])

            if prepared_forced:
                new_forced_index = existing_subtitle_count + 1
                output_args.extend([f"-metadata:s:s:{new_forced_index}", f"language={language}"])
                output_args.extend([f"-disposition:s:{new_forced_index}", "forced"])

            label = f"[MUX LEGENDA] {file_path.name}"
            run_with_spinner([*input_args, *output_args, out_file], label)
        finally:
            for temp_path in (subtitle_temp, forced_temp):
                if temp_path and temp_path.exists():
                    temp_path.unlink(missing_ok=True)


def mux_external_audio(
    work_dir: Path,
    tools: FfmpegTools,
    language: str = "por",
    make_default: bool = False,
    delay_ms: int = 0,
) -> None:
    videos = list_video_files(work_dir)
    if not videos:
        print("[AVISO] Nenhum video encontrado na pasta atual.")
        return

    out_dir = work_dir / "Saida" / "Audio" / "Mux_Externo"
    ensure_dir(out_dir)
    offset = f"{delay_ms / 1000:.3f}"

    for file_path in videos:
        external_audio = _find_external_audio(work_dir, file_path.stem)
        if not external_audio:
            print(f"[PULADO] {file_path.name} - audio externo com mesmo nome nao encontrado")
            continue

        out_file = out_dir / f"{file_path.stem}.mkv"
        if out_file.exists():
            print(f"[PULADO] {file_path.name} - arquivo de saida ja existe")
            continue

        existing_audio_count = len(_audio_streams(tools, file_path))
        args: list[str | Path] = [
            tools.ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-nostats",
            "-i",
            file_path,
            "-itsoffset",
            offset,
            "-i",
            external_audio,
            "-map",
            "0",
            "-map",
            "1:a:0",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c",
            "copy",
        ]

        if language:
            args.extend([f"-metadata:s:a:{existing_audio_count}", f"language={language}"])

        if make_default:
            args.extend(["-disposition:a", "0", f"-disposition:a:{existing_audio_count}", "default"])

        run_with_spinner([*args, out_file], f"[MUX AUDIO] {file_path.name}")
