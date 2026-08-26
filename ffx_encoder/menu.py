from __future__ import annotations

import os
from pathlib import Path

from .audio_subtitles import (
    edit_tracks_manual,
    extract_audio,
    extract_subtitles,
    generate_tracks_report,
    keep_only_audio_track,
    keep_portuguese_audio,
    keep_pt_en_audio_with_pt_subtitles,
    mux_external_audio,
    mux_external_subtitles,
    organize_tracks,
    remove_subtitles,
    remove_subtitles_by_position,
)
from .config import AppConfig
from .console import enable_colors
from .converter import convert_videos, deinterlace_videos, filter_videos, upscale_videos_1080p
from .covers import apply_cover_from_cache, apply_cover_from_tmdb, apply_local_cover, remove_embedded_covers
from .ffmpeg_tools import detect_encoder_message, locate_ffmpeg
from .metadata import clean_metadata, insert_movie_metadata
from .smart_mode import run_movie_smart_mode


def clear_screen() -> None:
    os.system("cls")


def pause() -> None:
    input("\nPressione ENTER para continuar...")


def read_menu_choice(valid_options: set[str]) -> str:
    while True:
        value = input("Escolha: ").strip().lower()
        if value in valid_options:
            return value
        print("[AVISO] Opcao invalida.")


def print_header(config: AppConfig) -> None:
    print("=========================================================")
    print(f"  FFx Encoder v{config.version} BY DjManeca")
    print("=========================================================")


def run_protected(action) -> None:
    try:
        action()
    except Exception as exc:
        print()
        print(f"[ERRO] {exc}")
        pause()


def run_main_menu(work_dir: Path | None = None) -> None:
    enable_colors()
    config = AppConfig()
    work_dir = work_dir or Path.cwd()

    try:
        tools = locate_ffmpeg(config)
        encoder_status = detect_encoder_message(tools)
    except Exception as exc:
        clear_screen()
        print_header(config)
        print()
        print(f"[ERRO] {exc}")
        pause()
        return

    while True:
        clear_screen()
        print_header(config)
        print()
        print(f"Encoder: {encoder_status}")
        print()
        print("1 - Audio e Legendas")
        print("2 - Converter")
        print("3 - Upscale 1080p")
        print("4 - Deinterlace")
        print("5 - Denoise")
        print("6 - Remaster")
        print("7 - Capas")
        print("8 - Metadados")
        print("9 - Modo Inteligente (Filmes)")
        print("0 - Sair")
        print()

        option = read_menu_choice({"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"})

        if option == "1":
            run_protected(lambda: run_audio_subtitles_menu(work_dir, tools))
            continue

        if option == "2":
            run_protected(lambda: run_converter_menu(work_dir, tools))
            continue

        if option == "3":
            run_protected(lambda: run_upscale_menu(work_dir, tools))
            continue

        if option == "4":
            run_protected(lambda: run_deinterlace_menu(work_dir, tools))
            continue

        if option == "5":
            run_protected(lambda: run_denoise_menu(work_dir, tools))
            continue

        if option == "6":
            run_protected(lambda: run_remaster_menu(work_dir, tools))
            continue

        if option == "7":
            run_protected(lambda: run_covers_menu(work_dir, tools))
            continue

        if option == "8":
            run_protected(lambda: run_metadata_menu(work_dir, tools))
            continue

        if option == "9":
            run_protected(lambda: run_movie_smart_mode_menu(work_dir, tools))
            continue

        if option == "0":
            return

        print()
        print("[AVISO] Opcao invalida.")
        pause()


def run_movie_smart_mode_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  MODO INTELIGENTE (FILMES)...AGUARDE...")
    print("=========================================================")
    run_movie_smart_mode(work_dir, tools)
    pause()


def choose_language(default: str = "por") -> str | None:
    print("Idioma:")
    print("1 - por (Portugues)")
    print("2 - eng (Ingles)")
    print("3 - spa (Espanhol)")
    print("4 - Digitar codigo")
    print("5 - Voltar")
    option = read_menu_choice({"1", "2", "3", "4", "5"})
    if option == "5":
        return None
    if option == "1" or option == "":
        return "por"
    if option == "2":
        return "eng"
    if option == "3":
        return "spa"
    if option == "4":
        typed = input("Codigo: ").strip()
        return typed or default
    return default


def choose_delay_ms(title: str = "ATRASO DA LEGENDA EXTERNA") -> int:
    clear_screen()
    print("=========================================================")
    print(f"  {title}")
    print("=========================================================")
    print()
    print("Use milissegundos. Valor positivo atrasa; valor negativo adianta.")
    print("Exemplos: 1000 atrasa 1 segundo, -1000 adianta 1 segundo.")
    print()
    raw = input("Atraso/adiantamento em ms (0 padrao, negativo adianta): ").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        print("[AVISO] Valor invalido. Usando 0 ms.")
        return 0


def choose_default_track() -> bool | None:
    clear_screen()
    print("=========================================================")
    print("  FAIXA DEFAULT")
    print("=========================================================")
    print()
    print("1 - Sim")
    print("2 - Nao")
    print("3 - Voltar")
    option = read_menu_choice({"1", "2", "3"})
    if option == "3":
        return None
    return option == "1"


def run_audio_subtitles_menu(work_dir: Path, tools) -> None:
    while True:
        clear_screen()
        print("=========================================================")
        print("  MENU DE AUDIO E LEGENDAS")
        print("=========================================================")
        print()
        print("1 - Manter apenas o audio 1")
        print("2 - Manter apenas o audio 2")
        print("3 - Manter apenas audio PT")
        print("4 - Manter PT+EN e legenda PT")
        print("5 - Juntar video + legenda externa (sem recode)")
        print("6 - Extrair audio")
        print("7 - Juntar audio externo")
        print("8 - Extrair legendas")
        print("9 - Remover legendas")
        print("10 - Gerar relatorio de faixas")
        print("11 - Organizar faixas")
        print("12 - Editor de faixas")
        print("13 - Voltar")
        print()

        option = read_menu_choice({"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"})

        if option == "1":
            clear_screen()
            print("=========================================================")
            print("  MANTENDO APENAS O AUDIO 1...AGUARDE...")
            print("=========================================================")
            keep_only_audio_track(work_dir, tools, 1)
            pause()
            return

        if option == "2":
            clear_screen()
            print("=========================================================")
            print("  MANTENDO APENAS O AUDIO 2...AGUARDE...")
            print("=========================================================")
            keep_only_audio_track(work_dir, tools, 2)
            pause()
            return

        if option == "3":
            clear_screen()
            print("=========================================================")
            print("  MANTENDO APENAS AUDIO PT...AGUARDE...")
            print("=========================================================")
            keep_portuguese_audio(work_dir, tools)
            pause()
            return

        if option == "4":
            clear_screen()
            print("=========================================================")
            print("  PROCESSANDO PT+EN E LEGENDA PT...AGUARDE...")
            print("=========================================================")
            keep_pt_en_audio_with_pt_subtitles(work_dir, tools)
            pause()
            return

        if option == "5":
            clear_screen()
            print("=========================================================")
            print("  JUNTANDO VIDEO + LEGENDA EXTERNA...AGUARDE...")
            print("=========================================================")
            language = choose_language("por")
            if language is None:
                return
            delay_ms = choose_delay_ms("ATRASO DA LEGENDA EXTERNA")
            mux_external_subtitles(work_dir, tools, language, delay_ms)
            pause()
            return

        if option == "6":
            run_extract_audio_menu(work_dir, tools)
            return

        if option == "7":
            run_mux_external_audio_menu(work_dir, tools)
            return

        if option == "8":
            run_extract_subtitles_menu(work_dir, tools)
            return

        if option == "9":
            run_remove_subtitles_menu(work_dir, tools)
            return

        if option == "10":
            clear_screen()
            print("=========================================================")
            print("  GERANDO RELATORIO DE FAIXAS...AGUARDE...")
            print("=========================================================")
            generate_tracks_report(work_dir, tools)
            pause()
            return

        if option == "11":
            clear_screen()
            print("=========================================================")
            print("  ORGANIZANDO FAIXAS...AGUARDE...")
            print("=========================================================")
            organize_tracks(work_dir, tools)
            pause()
            return

        if option == "12":
            clear_screen()
            print("=========================================================")
            print("  EDITOR DE FAIXAS")
            print("=========================================================")
            edit_tracks_manual(work_dir, tools)
            pause()
            return

        if option == "13":
            return

        print()
        print("[AVISO] Opcao invalida.")
        pause()


def run_converter_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  CONVERTER - CODEC")
    print("=========================================================")
    print()
    print("1 - H.265 / HEVC")
    print("2 - H.264 / AVC")
    print("3 - AV1")
    print("4 - Voltar")
    codec_option = read_menu_choice({"1", "2", "3", "4"})
    if codec_option == "4":
        return
    codec = {"1": "h265", "2": "h264", "3": "av1"}.get(codec_option, "h265")

    clear_screen()
    print("=========================================================")
    print("  CONVERTER - CONTAINER")
    print("=========================================================")
    print()
    print("1 - MKV")
    print("2 - MP4")
    print("3 - Voltar")
    container_option = read_menu_choice({"1", "2", "3"})
    if container_option == "3":
        return
    container = "mp4" if container_option == "2" else "mkv"

    clear_screen()
    print("=========================================================")
    print("  CONVERTER - AUDIO")
    print("=========================================================")
    print()
    print("1 - Copy")
    print("2 - AAC 224kbps")
    print("3 - Voltar")
    audio_option = read_menu_choice({"1", "2", "3"})
    if audio_option == "3":
        return
    audio_mode = "aac" if audio_option == "2" else "copy"

    clear_screen()
    print("=========================================================")
    print("  CONVERTER - QUALIDADE")
    print("=========================================================")
    print()
    print("1 - CQ/CRF 23 (maior qualidade)")
    print("2 - CQ/CRF 26 (equilibrado)")
    print("3 - CQ/CRF 28 (menor tamanho)")
    print("4 - Voltar")
    quality_option = read_menu_choice({"1", "2", "3", "4"})
    if quality_option == "4":
        return
    cq = {"1": "23", "2": "26", "3": "28"}.get(quality_option, "26")

    clear_screen()
    print("=========================================================")
    print("  CONVERTENDO...AGUARDE...")
    print("=========================================================")
    convert_videos(work_dir, tools, codec, container, audio_mode, cq)
    pause()


def run_upscale_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  UPSCALE 1080P - CODEC")
    print("=========================================================")
    print()
    print("1 - H.265 / HEVC")
    print("2 - H.264 / AVC")
    print("3 - AV1")
    print("4 - Voltar")
    codec_option = read_menu_choice({"1", "2", "3", "4"})
    if codec_option == "4":
        return
    codec = {"1": "h265", "2": "h264", "3": "av1"}.get(codec_option, "h265")

    clear_screen()
    print("=========================================================")
    print("  UPSCALE 1080P - CONTAINER")
    print("=========================================================")
    print()
    print("1 - MKV")
    print("2 - MP4")
    print("3 - Voltar")
    container_option = read_menu_choice({"1", "2", "3"})
    if container_option == "3":
        return
    container = "mp4" if container_option == "2" else "mkv"

    clear_screen()
    print("=========================================================")
    print("  UPSCALE 1080P - AUDIO")
    print("=========================================================")
    print()
    print("1 - Copy")
    print("2 - AAC 224kbps")
    print("3 - Voltar")
    audio_option = read_menu_choice({"1", "2", "3"})
    if audio_option == "3":
        return
    audio_mode = "aac" if audio_option == "2" else "copy"

    clear_screen()
    print("=========================================================")
    print("  UPSCALE 1080P - QUALIDADE")
    print("=========================================================")
    print()
    print("1 - CQ/CRF 23 (maior qualidade)")
    print("2 - CQ/CRF 26 (equilibrado)")
    print("3 - CQ/CRF 28 (menor tamanho)")
    print("4 - Voltar")
    quality_option = read_menu_choice({"1", "2", "3", "4"})
    if quality_option == "4":
        return
    cq = {"1": "23", "2": "26", "3": "28"}.get(quality_option, "26")

    clear_screen()
    print("=========================================================")
    print("  REALIZANDO UPSCALING...AGUARDE...")
    print("=========================================================")
    upscale_videos_1080p(work_dir, tools, codec, container, audio_mode, cq)
    pause()


def run_deinterlace_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  DEINTERLACE")
    print("=========================================================")
    print()
    print("1 - Manter resolucao original")
    print("2 - Upscaling para 1080p (Lanczos)")
    print("3 - Voltar")
    option = read_menu_choice({"1", "2", "3"})
    if option == "3":
        return
    upscale_to_1080 = option == "2"

    clear_screen()
    print("=========================================================")
    print("  DEINTERLACE - AUDIO")
    print("=========================================================")
    print()
    print("1 - Copy")
    print("2 - AAC 224kbps")
    print("3 - Voltar")
    audio_option = read_menu_choice({"1", "2", "3"})
    if audio_option == "3":
        return
    audio_mode = "aac" if audio_option == "2" else "copy"

    clear_screen()
    print("=========================================================")
    print("  PROCESSO DE DEINTERLACING COMECOU...AGUARDE...")
    print("=========================================================")
    deinterlace_videos(work_dir, tools, upscale_to_1080, audio_mode)
    pause()


def run_denoise_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("===============================")
    print("  REDUCAO DE GRANULADO")
    print("===============================")
    print()
    print("1 - Leve")
    print("2 - Medio")
    print("3 - Forte")
    print("4 - Voltar")
    option = read_menu_choice({"1", "2", "3", "4"})
    if option == "4":
        return
    filters = {
        "1": "hqdn3d=1.5:1.5:6:6",
        "2": "hqdn3d=3:3:6:6",
        "3": "hqdn3d=6:6:12:12",
    }
    video_filter = filters.get(option, filters["1"])

    clear_screen()
    print("=========================================================")
    print("  DENOISE - AUDIO")
    print("=========================================================")
    print()
    print("1 - Copy")
    print("2 - AAC 224kbps")
    print("3 - Voltar")
    audio_option = read_menu_choice({"1", "2", "3"})
    if audio_option == "3":
        return
    audio_mode = "aac" if audio_option == "2" else "copy"
    cq = "28" if audio_mode == "aac" else "26"

    clear_screen()
    print("=========================================================")
    print("  PROCESSANDO DENOISE...AGUARDE...")
    print("=========================================================")
    filter_videos(work_dir, tools, "DENOISE", "Denoise", video_filter, audio_mode, cq)
    pause()


def run_remaster_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("===============================")
    print("  REMASTER DE VIDEOS")
    print("===============================")
    print()
    print("1 - Remaster LEVE (recomendado)")
    print("2 - Remaster MEDIO")
    print("3 - Remaster FORTE")
    print("4 - Voltar")
    option = read_menu_choice({"1", "2", "3", "4"})
    if option == "4":
        return
    filters = {
        "1": "hqdn3d=1:1:4:4,unsharp=3:3:0.5:3:3:0.0",
        "2": "hqdn3d=1.5:1.5:6:6,unsharp=5:5:1.0:5:5:0.0,eq=contrast=1.1:brightness=0.02:saturation=1.1",
        "3": "hqdn3d=3:3:9:9,unsharp=7:7:1.5:7:7:0.0,eq=contrast=1.2:brightness=0.03:saturation=1.2",
    }
    video_filter = filters.get(option, filters["1"])

    clear_screen()
    print("=========================================================")
    print("  PROCESSANDO REMASTER...AGUARDE...")
    print("=========================================================")
    filter_videos(work_dir, tools, "REMASTER", "Remaster", video_filter, "copy", "26")
    pause()


def run_extract_audio_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  EXTRAIR AUDIO")
    print("=========================================================")
    print()
    print("1 - Audio 1")
    print("2 - Audio 2")
    print("3 - Audio PT")
    print("4 - Todos os audios")
    print("5 - Voltar")
    print()
    selector_option = read_menu_choice({"1", "2", "3", "4", "5"})
    if selector_option == "5":
        return
    selector = {
        "1": "audio1",
        "2": "audio2",
        "3": "pt",
        "4": "all",
    }.get(selector_option, "audio1")

    clear_screen()
    print("=========================================================")
    print("  FORMATO DO AUDIO EXTRAIDO")
    print("=========================================================")
    print()
    print("Formato de saida:")
    print("1 - Original (copy)")
    print("2 - AAC 224kbps (.m4a)")
    print("3 - MP3 320kbps")
    print("4 - Voltar")
    format_option = read_menu_choice({"1", "2", "3", "4"})
    if format_option == "4":
        return
    audio_format = {
        "1": "copy",
        "2": "aac",
        "3": "mp3",
    }.get(format_option, "copy")

    clear_screen()
    print("=========================================================")
    print("  EXTRAINDO AUDIO...AGUARDE...")
    print("=========================================================")
    extract_audio(work_dir, tools, selector, audio_format)
    pause()


def run_extract_subtitles_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  EXTRAIR LEGENDAS")
    print("=========================================================")
    print()
    print("1 - Escolher legendas manualmente")
    print("2 - Extrair todas as legendas")
    print("3 - Voltar")
    print()
    option = read_menu_choice({"1", "2", "3"})
    if option == "3":
        return

    clear_screen()
    print("=========================================================")
    print("  EXTRAINDO LEGENDAS...AGUARDE...")
    print("=========================================================")
    extract_subtitles(work_dir, tools, extract_all=option == "2")
    pause()


def run_remove_subtitles_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  REMOVER LEGENDAS")
    print("=========================================================")
    print()
    print("1 - Escolher por arquivo")
    print("2 - Remover mesma posicao do lote")
    print("3 - Voltar")
    print()
    option = read_menu_choice({"1", "2", "3"})
    if option == "3":
        return

    if option == "1":
        clear_screen()
        print("=========================================================")
        print("  REMOVENDO LEGENDAS...AGUARDE...")
        print("=========================================================")
        remove_subtitles(work_dir, tools)
        pause()
        return

    clear_screen()
    print("=========================================================")
    print("  REMOVER LEGENDAS EM LOTE")
    print("=========================================================")
    print()
    print("Remove a mesma posicao de legenda em todos os videos.")
    print("Exemplo: 2 remove a segunda faixa de legenda de cada arquivo.")
    print("Arquivos que nao tiverem essa posicao serao pulados.")
    print()
    raw = input("Posicao da legenda para remover: ").strip()
    try:
        position = int(raw)
    except ValueError:
        print("[AVISO] Posicao invalida.")
        pause()
        return

    clear_screen()
    print("=========================================================")
    print("  REMOVENDO LEGENDAS EM LOTE...AGUARDE...")
    print("=========================================================")
    remove_subtitles_by_position(work_dir, tools, position)
    pause()


def run_mux_external_audio_menu(work_dir: Path, tools) -> None:
    clear_screen()
    print("=========================================================")
    print("  JUNTAR AUDIO EXTERNO")
    print("=========================================================")
    print()
    print("O audio externo precisa estar na mesma pasta e com o mesmo nome do video.")
    print("Exemplo: Filme.mkv + Filme.m4a")
    print()
    language = choose_language("por")
    if language is None:
        return
    make_default = choose_default_track()
    if make_default is None:
        return

    delay_ms = choose_delay_ms("ATRASO DO AUDIO EXTERNO")

    clear_screen()
    print("=========================================================")
    print("  JUNTANDO AUDIO EXTERNO...AGUARDE...")
    print("=========================================================")
    mux_external_audio(work_dir, tools, language, make_default, delay_ms)
    pause()


def run_metadata_menu(work_dir: Path, tools) -> None:
    while True:
        clear_screen()
        print("=========================================================")
        print("  METADADOS")
        print("=========================================================")
        print()
        print("1 - Limpar metadados")
        print("2 - Inserir metadados de filme (TMDb)")
        print("3 - Voltar")
        print()

        option = read_menu_choice({"1", "2", "3"})

        if option == "1":
            clear_screen()
            print("=========================================================")
            print("  LIMPANDO METADADOS...AGUARDE...")
            print("=========================================================")
            clean_metadata(work_dir, tools)
            pause()
            return

        if option == "2":
            clear_screen()
            print("=========================================================")
            print("  BUSCANDO METADADOS DE FILME...AGUARDE...")
            print("=========================================================")
            insert_movie_metadata(work_dir, tools)
            pause()
            return

        if option == "3":
            return

        print()
        print("[AVISO] Opcao invalida.")
        pause()


def run_covers_menu(work_dir: Path, tools) -> None:
    while True:
        clear_screen()
        print("=========================================================")
        print("  CAPAS")
        print("=========================================================")
        print()
        print("1 - Usar cover local")
        print("2 - Buscar capa automaticamente (TMDb)")
        print("3 - Digitar nome para busca (TMDb)")
        print("4 - Buscar do cache")
        print("5 - Remover capas embutidas")
        print("6 - Voltar")
        print()

        option = read_menu_choice({"1", "2", "3", "4", "5", "6"})

        if option == "1":
            clear_screen()
            print("=========================================================")
            print("  ADICIONANDO CAPAS AOS VIDEOS...AGUARDE...")
            print("=========================================================")
            apply_local_cover(work_dir, tools)
            pause()
            return

        if option == "2":
            clear_screen()
            print("=========================================================")
            print("  BUSCANDO CAPA NO TMDB...AGUARDE...")
            print("=========================================================")
            apply_cover_from_tmdb(work_dir, tools, manual=False)
            pause()
            return

        if option == "3":
            clear_screen()
            print("=========================================================")
            print("  BUSCANDO CAPA NO TMDB...AGUARDE...")
            print("=========================================================")
            apply_cover_from_tmdb(work_dir, tools, manual=True)
            pause()
            return

        if option == "4":
            clear_screen()
            print("=========================================================")
            print("  BUSCANDO CAPA NO CACHE...AGUARDE...")
            print("=========================================================")
            apply_cover_from_cache(work_dir, tools)
            pause()
            return

        if option == "5":
            clear_screen()
            print("=========================================================")
            print("  REMOVENDO CAPAS EMBUTIDAS...AGUARDE...")
            print("=========================================================")
            remove_embedded_covers(work_dir, tools)
            pause()
            return

        if option == "6":
            return

        print()
        print("[AVISO] Opcao invalida.")
        pause()
