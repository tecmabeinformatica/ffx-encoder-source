from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ffx_encoder.config import AppConfig
from ffx_encoder.covers import _cached_cover_path, _detect_cache_query
from ffx_encoder.ffmpeg_tools import FfmpegTools, detect_encoder_message, locate_ffmpeg, video_encoder_args
from ffx_encoder.media import VIDEO_EXTENSIONS, ensure_dir
from ffx_encoder.metadata import GLOBAL_METADATA_KEYS, _safe_name
from ffx_encoder.tmdb import download_poster, search_movies, search_multi, season_details


GUI_VERSION = "2.1"
MIN_WINDOW_WIDTH = 1600
MIN_WINDOW_HEIGHT = 980
DEFAULT_WINDOW_WIDTH = 1600
DEFAULT_WINDOW_HEIGHT = 980
BOTTOM_TOOLS_HEIGHT = 570
METADATA_PANEL_HEIGHT = 350
COVER_PREVIEW_WIDTH = 165
COVER_PREVIEW_HEIGHT = 235
COVER_PREVIEW_FRAME_PAD_X = 24
COVER_PREVIEW_FRAME_PAD_Y = 42
RESOLUTION_OPTIONS = ("Original", "480p", "720p", "1080p", "1440p", "2160p", "Personalizada")
BORDER_RESOLUTION_OPTIONS = ("Manter", "480p", "720p", "1080p", "1440p", "2160p", "Personalizada")
AUDIO_OPTIONS = ("copy", "AAC 256 kbps", "AAC 320 kbps", "AC3 640 kbps")
REMASTER_AUDIO_OPTIONS = ("copy", "AAC 256 kbps", "AAC 320 kbps", "AC3 640 kbps")
TMDB_QUERY_PLACEHOLDER_PT = "Digite aqui o nome do filme ou série"
TMDB_QUERY_PLACEHOLDER_EN = "Type movie or series name here"
TMDB_BUTTON_WIDTH = 18
TMDB_RESULTS_WIDTH = 1100
PROCESSING_TOOLS_WIDTH = 1200
IMAGE_VIDEO_CODECS = {"mjpeg", "png", "apng", "webp", "bmp", "gif", "jpeg2000"}
COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png")
AUDIO_EXTENSIONS = (".m4a", ".aac", ".mp3", ".ac3", ".eac3", ".dts", ".flac", ".opus", ".ogg", ".wav", ".mka")
SUBTITLE_EXTENSIONS = (".srt", ".ass", ".ssa")

UI_EN = {
    "Arquivo": "File",
    "Carregar pasta...": "Load folder...",
    "Carregar arquivo...": "Load file...",
    "Sair": "Exit",
    "Configurações": "Settings",
    "Chave TMDb...": "TMDb key...",
    "Pastas de trabalho...": "Work folders...",
    "Tema": "Theme",
    "Modo claro": "Light mode",
    "Modo escuro": "Dark mode",
    "Idioma": "Language",
    "Ajuda": "Help",
    "Leia-me": "Read me",
    "Sobre": "About",
    "Pasta:": "Folder:",
    "Selecionar": "Select",
    "Recarregar": "Reload",
    "Vídeos": "Videos",
    "Conteúdo": "Content",
    "Status": "Status",
    "Faixa": "Track",
    "Codec": "Codec",
    "Flags": "Flags",
    "Titulo/Info": "Title/Info",
    "Ações rápidas": "Quick actions",
    "Manter/Remover": "Keep/Remove",
    "Mover Acima": "Move Up",
    "Mover Abaixo": "Move Down",
    "Default": "Default",
    "Forced": "Forced",
    "Remover Imagens": "Remove Images",
    "Remover Legendas": "Remove Subtitles",
    "Remover Anexos": "Remove Attachments",
    "Manter Tudo": "Keep All",
    "Aplicar": "Apply",
    "Ferramentas de processamento": "Processing tools",
    "Áudio": "Audio",
    "Legendas": "Subtitles",
    "Limpeza": "Cleanup",
    "Conversão": "Conversion",
    "Remaster": "Remaster",
    "Filtros": "Filters",
    "Corrigir Aspecto": "Fix Aspect",
    "Corrigir Bordas": "Fix Borders",
    "Modo Inteligente": "Smart Mode",
    "Relatórios": "Reports",
    "Áudio 1": "Audio 1",
    "Áudio 2": "Audio 2",
    "Áudio PT": "PT Audio",
    "Extrair Áudios": "Extract Audio",
    "Extrair Áudio Opções": "Audio Extract Options",
    "Juntar Áudio": "Add Audio",
    "Remover Legenda Nº": "Remove Subtitle #",
    "Extrair Legendas": "Extract Subtitles",
    "Extrair Legenda Opções": "Subtitle Extract Options",
    "Juntar Legenda": "Add Subtitle",
    "Remover Imagens": "Remove Images",
    "Organizar PT/EN": "Organize PT/EN",
    "Buscar Filme": "Search Movie",
    "Modo Inteligente Filme": "Smart Movie Mode",
    "Buscar Série": "Search Series",
    "Modo Inteligente Série": "Smart Series Mode",
    "Gerar Relatório": "Generate Report",
    "Verificar Vídeo": "Check Video",
    "Metadados e capas": "Metadata and covers",
    "Nome:": "Name:",
    "Buscar": "Search",
    "Limpar": "Clear",
    "Aplicar Metadados": "Apply Metadata",
    "Limpar Metadados": "Clear Metadata",
    "Prévia capa": "Cover preview",
    "Aplicar capa": "Apply cover",
    "Remover capa": "Remove cover",
    "Cover local": "Local cover",
    "Cover cache": "Cache cover",
    "Prévia": "Preview",
    "Sem prévia": "No preview",
    "Processos": "Processes",
    "Abrir saída": "Open output",
    "Cancelar processo": "Cancel process",
    "Áudio:": "Audio:",
    "Qualidade:": "Quality:",
    "Resolução:": "Resolution:",
    "Filtro:": "Filter:",
    "Processar": "Process",
    "Aspecto:": "Aspect:",
    "Tentar sem recode": "Try without recode",
    "Corrigir": "Fix",
    "Analisar": "Analyze",
    "Modo:": "Mode:",
    "Cortar:": "Crop:",
    "Automatico agressivo": "Aggressive automatic",
    "Manual": "Manual",
    "Manter": "Keep",
    "Esq": "Left",
    "Dir": "Right",
    "Topo": "Top",
    "Baixo": "Bottom",
    "Tipo:": "Type:",
    "Aplicar Filtro": "Apply Filter",
    "Remover bordas pretas": "Remove black borders",
    "Remasterizar": "Remaster",
    "Normalizar volume": "Normalize volume",
}
FILTER_LABELS_EN = {
    "None": "None",
    "Deinterlace": "Deinterlace",
    "Denoise leve": "Light denoise",
    "Denoise medio": "Medium denoise",
    "Denoise forte": "Strong denoise",
    "Granulado leve": "Light grain",
    "Granulado medio": "Medium grain",
    "Granulado forte": "Strong grain",
    "Remaster leve": "Light remaster",
    "Remaster medio": "Medium remaster",
    "Remaster forte": "Strong remaster",
}
FILTER_VALUES_BY_LABEL_EN = {label: value for value, label in FILTER_LABELS_EN.items()}


class CancelledProcess(Exception):
    pass


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.after_id: str | None = None
        self.window: tk.Toplevel | None = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def schedule(self, _event: tk.Event | None = None) -> None:
        self.cancel()
        self.after_id = self.widget.after(self.delay_ms, self.show)

    def cancel(self) -> None:
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

    def show(self) -> None:
        if self.window is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.window,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=5,
            wraplength=360,
        )
        label.pack()

    def hide(self, _event: tk.Event | None = None) -> None:
        self.cancel()
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None


def run_hidden(args: list[str | Path]) -> subprocess.CompletedProcess[str]:
    startupinfo = None
    creationflags = 0
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(
        [str(arg) for arg in args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=startupinfo,
        creationflags=creationflags,
    )


def ffprobe_streams(tools: FfmpegTools, file_path: Path) -> list[dict]:
    result = run_hidden([
        tools.ffprobe,
        "-v",
        "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,channels,bit_rate:stream_tags=language,title,filename,mimetype:stream_disposition=default,forced,hearing_impaired",
        "-of",
        "json",
        file_path,
    ])
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        return json.loads(result.stdout).get("streams", [])
    except json.JSONDecodeError:
        return []


def stream_language(stream: dict) -> str:
    return str(stream.get("tags", {}).get("language", "") or "und").lower()


def stream_title(stream: dict) -> str:
    tags = stream.get("tags", {})
    return str(
        tags.get("title")
        or tags.get("TITLE")
        or tags.get("filename")
        or tags.get("FILENAME")
        or tags.get("mimetype")
        or tags.get("MIMETYPE")
        or ""
    ).strip()


def disposition(stream: dict, name: str) -> bool:
    return int(stream.get("disposition", {}).get(name, 0) or 0) == 1


def audio_extension(codec: str) -> str:
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
    }.get(codec.lower(), ".mka")


def subtitle_extension(codec: str) -> str:
    return {
        "subrip": ".srt",
        "ass": ".ass",
        "ssa": ".ssa",
        "webvtt": ".vtt",
        "hdmv_pgs_subtitle": ".sup",
        "dvd_subtitle": ".sub",
    }.get(codec.lower(), ".srt")


def find_sidecar(file_path: Path, extensions: tuple[str, ...]) -> Path | None:
    for extension in extensions:
        candidate = file_path.with_suffix(extension)
        if candidate.exists():
            return candidate
    return None


def find_subtitle_sidecars(file_path: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    for extension in SUBTITLE_EXTENSIONS:
        exact = file_path.with_suffix(extension)
        if exact.exists():
            candidates.append(exact)
            seen.add(exact.resolve())
        for candidate in sorted(file_path.parent.glob(f"{file_path.stem}.*{extension}")):
            resolved = candidate.resolve()
            if resolved not in seen:
                candidates.append(candidate)
                seen.add(resolved)
    return sorted(candidates, key=lambda path: (0 if subtitle_sidecar_is_forced(path) else 1, path.name.lower()))


def subtitle_sidecar_is_forced(subtitle_path: Path) -> bool:
    return "forced" in subtitle_path.stem.lower().split(".")


def subtitle_sidecar_language(subtitle_path: Path, fallback: str) -> str:
    aliases = {
        "por": "por",
        "pt": "por",
        "pt-br": "por",
        "pob": "por",
        "pb": "por",
        "br": "por",
        "eng": "eng",
        "en": "eng",
        "spa": "spa",
        "es": "spa",
    }
    for token in subtitle_path.stem.lower().split("."):
        if token in aliases:
            return aliases[token]
    return fallback.strip().lower()[:3] or "por"


class TrackEditorApp(tk.Tk):
    def __init__(self, initial_dir: Path | None = None) -> None:
        super().__init__()
        self.title(f"FFX Encoder GUI {GUI_VERSION}")
        self.geometry(self.centered_geometry(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT))
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.config_data = AppConfig()
        self.tools = locate_ffmpeg(self.config_data)
        self.work_dir = initial_dir if initial_dir and initial_dir.exists() else Path.cwd()
        self.video_files: list[Path] = []
        self.current_file: Path | None = None
        self.tracks: list[dict] = []
        self.tmdb_results: list[dict] = []
        self.tmdb_result_mode = "cover"
        self.action_buttons: list[ttk.Button] = []
        self.tmdb_buttons: list[ttk.Button] = []
        self.conversion_recode_widgets: list[tk.Widget] = []
        self.apply_metadata_button: ttk.Button | None = None
        self.cancel_event = threading.Event()
        self.active_process: subprocess.Popen[str] | None = None
        self.encoder_message = ""
        self.codec_var = tk.StringVar(value="H.265 / HEVC")
        self.audio_mode_var = tk.StringVar(value="copy")
        self.resolution_var = tk.StringVar(value="Original")
        self.container_var = tk.StringVar(value="MKV")
        self.quality_var = tk.StringVar(value="CQ/CRF 28")
        self.filter_only_type_var = tk.StringVar(value="Deinterlace")
        self.filter_only_audio_var = tk.StringVar(value="copy")
        self.filter_only_quality_var = tk.StringVar(value="CQ/CRF 23")
        self.aspect_target_var = tk.StringVar(value="4:3")
        self.aspect_container_var = tk.StringVar(value="MKV")
        self.aspect_audio_var = tk.StringVar(value="copy")
        self.aspect_quality_var = tk.StringVar(value="CQ/CRF 23")
        self.aspect_copy_first_var = tk.BooleanVar(value=True)
        self.borders_mode_var = tk.StringVar(value="Automatico agressivo")
        self.borders_codec_var = tk.StringVar(value="H.265 / HEVC")
        self.borders_container_var = tk.StringVar(value="MKV")
        self.borders_audio_var = tk.StringVar(value="copy")
        self.borders_quality_var = tk.StringVar(value="CQ/CRF 23")
        self.borders_resolution_var = tk.StringVar(value="Manter")
        self.borders_left_var = tk.StringVar(value="0")
        self.borders_right_var = tk.StringVar(value="0")
        self.borders_top_var = tk.StringVar(value="0")
        self.borders_bottom_var = tk.StringVar(value="0")
        self.conversion_crop_var = tk.BooleanVar(value=False)
        self.filter_only_crop_var = tk.BooleanVar(value=False)
        self.remaster_crop_var = tk.BooleanVar(value=False)
        self.remaster_deinterlace_var = tk.BooleanVar(value=False)
        self.remaster_normalize_var = tk.BooleanVar(value=False)
        self.theme_var = tk.StringVar(value="Claro")
        self.language_var = tk.StringVar(value="Português")
        self.filter_var = tk.StringVar(value="None")
        self.conversion_deinterlace_var = tk.BooleanVar(value=False)
        self.auto_tmdb_on_folder_var = tk.BooleanVar(value=False)
        self.output_root_var = tk.StringVar(value="")
        self.temp_root_var = tk.StringVar(value="")
        self.overwrite_all_outputs = False
        self.last_auto_tmdb_dir: str | None = None
        self.last_output_dir: Path | None = None
        self.state_path = self.config_data.app_root / "gui_state.json"
        self.tmdb_placeholder_active = False
        self.main_pane: ttk.PanedWindow | None = None
        self.body_pane: ttk.PanedWindow | None = None
        self.right_pane: ttk.PanedWindow | None = None
        self.tmdb_pane: ttk.PanedWindow | None = None
        self.tools_bottom: ttk.Frame | None = None
        self.actions_frame: ttk.LabelFrame | None = None
        self.tmdb_frame: ttk.LabelFrame | None = None
        self.cover_preview_frame: ttk.LabelFrame | None = None
        self.cover_preview_image: tk.PhotoImage | None = None
        self.cover_preview_path: Path | None = None
        self.busy_indicator_after: str | None = None
        self.busy_indicator_on = False
        self.busy_indicator_active = False
        self.busy_indicator_color = "#2f75b5"
        self.busy_indicator_dim_color = "#9bbbd8"
        self.app_menu_bar: tk.Frame | None = None
        self.open_app_menu: tk.Toplevel | None = None

        self.load_initial_preferences()
        self._set_window_icon()
        self._build_ui()
        self._set_status()
        self.load_folder(self.work_dir)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.restore_gui_state)
        self.after(180, self.apply_default_pane_layout)

    def tr(self, text: str) -> str:
        if self.language_var.get() == "English":
            return UI_EN.get(text, text)
        return text

    def filter_label(self, value: str) -> str:
        if value == "Nenhum":
            return "None"
        if self.language_var.get() == "English":
            return FILTER_LABELS_EN.get(value, value)
        return value

    def filter_value(self) -> str:
        value = self.filter_var.get()
        if value == "None":
            return "Nenhum"
        if self.language_var.get() == "English":
            return FILTER_VALUES_BY_LABEL_EN.get(value, value)
        return value

    def normalize_filter_value(self, value: str) -> str:
        if value == "None":
            return "Nenhum"
        return FILTER_VALUES_BY_LABEL_EN.get(value, value)

    def load_initial_preferences(self) -> None:
        if not self.state_path.exists():
            return
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        theme = state.get("theme")
        if theme in {"Claro", "Escuro"}:
            self.theme_var.set(theme)
        language = state.get("language")
        if language in {"Português", "English"}:
            self.language_var.set(language)
        self.auto_tmdb_on_folder_var.set(bool(state.get("auto_tmdb_on_folder", False)))
        self.output_root_var.set(str(state.get("output_root", "") or ""))
        self.temp_root_var.set(str(state.get("temp_root", "") or ""))

    def centered_geometry(self, width: int, height: int) -> str:
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max((screen_width - width) // 2, 0)
        y = max((screen_height - height) // 2, 0)
        return f"{width}x{height}+{x}+{y}"

    def _set_window_icon(self) -> None:
        icon_candidates = [
            self.config_data.app_root / "icone.ico",
            Path(r"D:\scripts\imagens do projeto\icone.ico"),
        ]
        for icon_path in icon_candidates:
            if icon_path.exists():
                try:
                    self.iconbitmap(default=str(icon_path))
                    return
                except tk.TclError:
                    continue

    def on_close(self) -> None:
        self.save_gui_state()
        self.destroy()

    def save_gui_state(self) -> None:
        state = {
            "theme": self.theme_var.get(),
            "language": self.language_var.get(),
            "auto_tmdb_on_folder": bool(self.auto_tmdb_on_folder_var.get()),
            "output_root": self.output_root_var.get().strip(),
            "temp_root": self.temp_root_var.get().strip(),
        }
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError:
            pass

    def restore_gui_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        language = state.get("language")
        if language in {"Português", "English"} and self.language_var.get() != language:
            self.language_var.set(language)
        theme = state.get("theme")
        if theme in {"Claro", "Escuro"} and self.theme_var.get() != theme:
            self.theme_var.set(theme)
            self.apply_theme()
        self.auto_tmdb_on_folder_var.set(bool(state.get("auto_tmdb_on_folder", self.auto_tmdb_on_folder_var.get())))
        self.output_root_var.set(str(state.get("output_root", self.output_root_var.get()) or ""))
        self.temp_root_var.set(str(state.get("temp_root", self.temp_root_var.get()) or ""))

    def apply_default_pane_layout(self) -> None:
        """Mantem o painel de metadados com altura suficiente ao abrir."""
        try:
            self.update_idletasks()
            if self.main_pane is not None:
                self.main_pane.sashpos(0, max(self.main_pane.winfo_height() - 165, 520))
            if self.body_pane is not None:
                self.body_pane.sashpos(0, 260)
        except tk.TclError:
            pass

    def _build_menu(self) -> None:
        self.config(menu="")
        self.app_menu_bar = tk.Frame(self, bd=0, highlightthickness=0)
        self.app_menu_bar.pack(side=tk.TOP, fill=tk.X)
        for title, items in [
            (self.tr("Arquivo"), self.file_menu_items),
            (self.tr("Configurações"), self.config_menu_items),
            (self.tr("Ajuda"), self.help_menu_items),
        ]:
            button = tk.Label(self.app_menu_bar, text=title, padx=10, pady=5, cursor="hand2")
            button.pack(side=tk.LEFT)
            button.bind("<Button-1>", lambda _event, widget=button, factory=items: self.show_app_menu(widget, factory()))
        self.style_app_menu_bar()

    def _build_ui(self) -> None:
        self._build_menu()
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        self.folder_var = tk.StringVar(value=str(self.work_dir))
        ttk.Label(top, text=self.tr("Pasta:")).pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        button = ttk.Button(top, text=self.tr("Selecionar"), command=self.choose_folder)
        button.pack(side=tk.LEFT)
        self.add_tooltip(button, "Selecionar")
        button = ttk.Button(top, text=self.tr("Recarregar"), command=lambda: self.load_folder(Path(self.folder_var.get())))
        button.pack(side=tk.LEFT, padx=(6, 0))
        self.add_tooltip(button, "Recarregar")

        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.main_pane = main_pane
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        body = ttk.PanedWindow(main_pane, orient=tk.HORIZONTAL)
        self.body_pane = body
        main_pane.add(body, weight=7)

        left = ttk.Frame(body, padding=(0, 0, 8, 0))
        body.add(left, weight=2)
        ttk.Label(left, text=self.tr("Vídeos")).pack(anchor=tk.W)
        self.video_list = tk.Listbox(left, exportselection=False)
        self.video_list.pack(fill=tk.BOTH, expand=True)
        self.video_list.bind("<<ListboxSelect>>", lambda _event: self.load_selected_video())

        right = ttk.Frame(body)
        body.add(right, weight=8)

        self.right_pane = None

        tools_pane = ttk.Frame(right, height=BOTTOM_TOOLS_HEIGHT)
        tools_pane.pack(side=tk.BOTTOM, fill=tk.X)
        tools_pane.pack_propagate(False)

        editor_pane = ttk.Frame(right)
        editor_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tools_bottom = ttk.Frame(tools_pane)
        self.tools_bottom = tools_bottom
        tools_bottom.pack(side=tk.BOTTOM, fill=tk.X)

        content_frame = ttk.LabelFrame(editor_pane, text=self.tr("Conteúdo"), padding=6)
        content_frame.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("status", "type", "codec", "language", "flags", "title")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("status", text=self.tr("Status"), anchor=tk.W)
        self.tree.heading("type", text=self.tr("Faixa"), anchor=tk.W)
        self.tree.heading("codec", text=self.tr("Codec"), anchor=tk.W)
        self.tree.heading("language", text=self.tr("Idioma"), anchor=tk.W)
        self.tree.heading("flags", text=self.tr("Flags"), anchor=tk.W)
        self.tree.heading("title", text=self.tr("Titulo/Info"), anchor=tk.W)
        self.tree.column("status", width=70, anchor=tk.W)
        self.tree.column("type", width=95, anchor=tk.W)
        self.tree.column("codec", width=90, anchor=tk.W)
        self.tree.column("language", width=70, anchor=tk.W)
        self.tree.column("flags", width=120, anchor=tk.W)
        self.tree.column("title", width=280, anchor=tk.W)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        quick_actions = ttk.LabelFrame(tools_bottom, text=self.tr("Ações rápidas"), padding=6)
        quick_actions.pack(fill=tk.X, pady=(6, 0))
        buttons = ttk.Frame(quick_actions)
        buttons.pack(fill=tk.X)
        for text, command in [
            ("Manter/Remover", self.toggle_selected),
            ("Mover Acima", lambda: self.move_selected(-1)),
            ("Mover Abaixo", lambda: self.move_selected(1)),
            ("Idioma", self.change_language),
            ("Default", self.set_default),
            ("Forced", self.toggle_forced),
            ("Remover Imagens", self.remove_image_videos),
            ("Remover Legendas", self.remove_subtitles),
            ("Remover Anexos", self.remove_attachments),
            ("Manter Tudo", self.keep_all),
            ("Aplicar", self.apply_changes),
        ]:
            button = ttk.Button(buttons, text=self.tr(text), command=command)
            button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
            self.add_tooltip(button, text)
            self.action_buttons.append(button)
        actions = ttk.LabelFrame(tools_bottom, text=self.tr("Ferramentas de processamento"), padding=6)
        self.actions_frame = actions
        actions.pack(side=tk.TOP, anchor=tk.W, fill=tk.X, pady=(0, 6))
        actions.configure(height=118)
        actions.pack_propagate(False)
        actions.configure(width=PROCESSING_TOOLS_WIDTH)
        action_tabs = ttk.Notebook(actions)
        action_tabs.pack(anchor=tk.W, fill=tk.X)

        self._add_action_tab(action_tabs, "Áudio", [
            ("Áudio 1", lambda: self.keep_tracks_preset_batch("audio1")),
            ("Áudio 2", lambda: self.keep_tracks_preset_batch("audio2")),
            ("Áudio PT", lambda: self.keep_tracks_preset_batch("audio_pt")),
            ("Extrair Áudios", self.extract_audio_batch),
            ("Extrair Áudio Opções", self.extract_audio_options_batch),
            ("Juntar Áudio", self.mux_external_audio_batch),
        ])
        self._add_action_tab(action_tabs, "Legendas", [
            ("Remover Legendas", self.remove_subtitles_batch),
            ("Remover Legenda Nº", self.remove_subtitle_position_batch),
            ("Extrair Legendas", self.extract_subtitles_batch),
            ("Extrair Legenda Opções", self.extract_subtitle_options_batch),
            ("Juntar Legenda", self.mux_external_subtitle_batch),
        ])
        self._add_action_tab(action_tabs, "Limpeza", [
            ("PT+EN + Legenda PT", lambda: self.keep_tracks_preset_batch("pt_en_sub_pt")),
            ("Remover Imagens", self.remove_image_videos_batch),
            ("Remover Anexos", self.remove_attachments_batch),
            ("Organizar PT/EN", self.organize_pt_en_batch),
        ])
        self._add_conversion_tab(action_tabs)
        self._add_aspect_tab(action_tabs)
        self._add_borders_tab(action_tabs)
        self._add_filters_tab(action_tabs)
        self._add_remaster_tab(action_tabs)
        self._add_action_tab(action_tabs, "Modo Inteligente", [
            ("Buscar Filme", self.search_tmdb_metadata_panel, True),
            ("Modo Inteligente Filme", self.smart_movie_mode_gui, True),
            ("Buscar Série", self.search_tmdb_cover_panel, True),
            ("Modo Inteligente Série", self.smart_series_mode_gui, True),
        ])
        self._add_action_tab(action_tabs, "Relatórios", [
            ("Gerar Relatório", self.generate_report),
            ("Verificar Vídeo", self.generate_video_check_report),
        ])

        tmdb_frame = ttk.LabelFrame(tools_bottom, text=self.tr("Metadados e capas"), padding=6)
        self.tmdb_frame = tmdb_frame
        tmdb_frame.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 0))
        tmdb_frame.configure(height=METADATA_PANEL_HEIGHT)
        tmdb_frame.pack_propagate(False)

        search_row = ttk.Frame(tmdb_frame)
        search_row.pack(fill=tk.X)
        ttk.Label(search_row, text=self.tr("Nome:")).pack(side=tk.LEFT, padx=(0, 4))
        self.tmdb_query_var = tk.StringVar()
        self.tmdb_entry = ttk.Entry(search_row, textvariable=self.tmdb_query_var, width=34)
        self.tmdb_entry.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=(0, 6))
        self.tmdb_entry.bind("<FocusIn>", self.clear_tmdb_placeholder)
        self.tmdb_entry.bind("<FocusOut>", self.show_tmdb_placeholder)
        self.show_tmdb_placeholder()
        button = ttk.Button(search_row, text=self.tr("Buscar"), width=12, command=self.search_tmdb_cover_panel)
        button.pack(side=tk.LEFT, padx=(0, 6))
        self.add_tooltip(button, "Buscar")
        self.action_buttons.append(button)
        self.tmdb_buttons.append(button)
        button = ttk.Button(search_row, text=self.tr("Limpar"), width=12, command=self.clear_tmdb_search)
        button.pack(side=tk.LEFT)
        self.add_tooltip(button, "Limpar")

        tmdb_buttons = ttk.Frame(search_row)
        tmdb_buttons.pack(side=tk.LEFT, padx=(8, 0))
        button = ttk.Button(tmdb_buttons, text=self.tr("Aplicar Metadados"), width=TMDB_BUTTON_WIDTH, command=self.apply_selected_tmdb_metadata)
        button.pack(side=tk.LEFT, padx=(0, 6))
        self.add_tooltip(button, "Aplicar Metadados")
        self.action_buttons.append(button)
        self.tmdb_buttons.append(button)
        self.apply_metadata_button = button
        button.configure(state=tk.DISABLED)
        button = ttk.Button(tmdb_buttons, text=self.tr("Limpar Metadados"), width=TMDB_BUTTON_WIDTH, command=self.clean_metadata_batch)
        button.pack(side=tk.LEFT, padx=(0, 0))
        self.add_tooltip(button, "Limpar Metadados")
        self.action_buttons.append(button)

        tmdb_body = ttk.Frame(tmdb_frame)
        tmdb_body.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        results_frame = ttk.Frame(tmdb_body)
        results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tmdb_list = tk.Listbox(results_frame, height=5, exportselection=False)
        self.tmdb_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tmdb_list.bind("<<ListboxSelect>>", lambda _event: self.update_apply_metadata_button_state())
        tmdb_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tmdb_list.yview)
        tmdb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tmdb_list.configure(yscrollcommand=tmdb_scroll.set)

        cover_buttons = ttk.Frame(tmdb_body)
        cover_buttons.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 8))
        button = ttk.Button(cover_buttons, text=self.tr("Prévia capa"), width=16, command=self.preview_selected_tmdb_cover)
        button.pack(fill=tk.X, pady=(0, 4))
        self.add_tooltip(button, "Prévia capa")
        self.action_buttons.append(button)
        self.tmdb_buttons.append(button)
        button = ttk.Button(cover_buttons, text=self.tr("Aplicar capa"), width=16, command=self.apply_selected_tmdb_cover)
        button.pack(fill=tk.X, pady=(0, 4))
        self.add_tooltip(button, "Aplicar capa")
        self.action_buttons.append(button)
        self.tmdb_buttons.append(button)
        button = ttk.Button(cover_buttons, text=self.tr("Remover capa"), width=16, command=self.remove_covers_batch)
        button.pack(fill=tk.X, pady=(0, 4))
        self.add_tooltip(button, "Remover capa")
        self.action_buttons.append(button)
        button = ttk.Button(cover_buttons, text=self.tr("Cover local"), width=16, command=self.apply_local_cover_batch)
        button.pack(fill=tk.X, pady=(0, 4))
        self.add_tooltip(button, "Cover local")
        self.action_buttons.append(button)
        button = ttk.Button(cover_buttons, text=self.tr("Cover cache"), width=16, command=self.apply_cache_cover_batch)
        button.pack(fill=tk.X, pady=(0, 0))
        self.add_tooltip(button, "Cover cache")
        self.action_buttons.append(button)

        preview_frame = ttk.LabelFrame(tmdb_body, text=self.tr("Prévia"), padding=4)
        self.cover_preview_frame = preview_frame
        preview_frame.pack(side=tk.RIGHT, fill=tk.NONE, expand=False, anchor=tk.N)
        preview_frame.configure(
            width=COVER_PREVIEW_WIDTH + COVER_PREVIEW_FRAME_PAD_X,
            height=COVER_PREVIEW_HEIGHT + COVER_PREVIEW_FRAME_PAD_Y,
        )
        preview_frame.pack_propagate(False)
        self.cover_preview_label = ttk.Label(preview_frame, text=self.tr("Sem prévia"), anchor=tk.CENTER)
        self.cover_preview_label.pack(fill=tk.BOTH, expand=True)
        self.cover_preview_label.bind("<Double-Button-1>", lambda _event: self.open_cover_preview())

        bottom = ttk.LabelFrame(main_pane, text=self.tr("Processos"), padding=6)
        main_pane.add(bottom, weight=0)
        self.status_var = tk.StringVar()
        process_top = ttk.Frame(bottom)
        process_top.pack(fill=tk.X)
        ttk.Label(process_top, textvariable=self.status_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        bottom_buttons = ttk.Frame(process_top)
        bottom_buttons.pack(side=tk.RIGHT, padx=(12, 0))
        indicator_frame = ttk.Frame(bottom_buttons)
        indicator_frame.pack(side=tk.LEFT, padx=(0, 10))
        self.busy_canvas = tk.Canvas(indicator_frame, width=16, height=16, highlightthickness=0, bd=0)
        self.busy_canvas.pack(side=tk.LEFT, padx=(0, 4))
        self.busy_dot = self.busy_canvas.create_oval(4, 4, 12, 12, fill="", outline="")
        self.busy_text = ttk.Label(indicator_frame, text="", width=16)
        self.busy_text.pack(side=tk.LEFT)
        self.open_output_button = ttk.Button(bottom_buttons, text=self.tr("Abrir saída"), command=self.open_last_output_dir, state=tk.DISABLED)
        self.open_output_button.pack(side=tk.LEFT, padx=(0, 6))
        self.cancel_button = ttk.Button(bottom_buttons, text=self.tr("Cancelar processo"), command=self.cancel_current_process, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT)
        log_frame = ttk.Frame(bottom)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.log = tk.Text(log_frame, height=6, wrap=tk.WORD)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.apply_theme()
        self.update_tmdb_button_states()

    def configure_menu_colors(self, menubar: tk.Menu, *menus: tk.Menu) -> None:
        dark = self.is_dark_theme()
        bg = "#202020" if dark else "#f0f0f0"
        fg = "#f4f4f4" if dark else "#202020"
        active_bg = "#333333" if dark else "#e7f1fb"
        active_fg = fg
        for menu in (menubar, *menus):
            try:
                menu.configure(
                    background=bg,
                    foreground=fg,
                    activebackground=active_bg,
                    activeforeground=active_fg,
                    borderwidth=0 if dark else 1,
                )
            except tk.TclError:
                pass

    def file_menu_items(self) -> list[dict]:
        return [
            {"label": self.tr("Carregar pasta..."), "command": self.choose_folder},
            {"label": self.tr("Carregar arquivo..."), "command": self.choose_file},
            {"separator": True},
            {"label": self.tr("Sair"), "command": self.on_close},
        ]

    def config_menu_items(self) -> list[dict]:
        return [
            {"label": self.tr("Chave TMDb..."), "command": self.configure_tmdb_key},
            {"label": self.tr("Pastas de trabalho..."), "command": self.configure_work_folders},
            {"separator": True},
            {"label": f"Busca automática TMDb {'✓' if self.auto_tmdb_on_folder_var.get() else ''}", "command": self.toggle_auto_tmdb_on_folder},
            {"separator": True},
            {"label": f"{self.tr('Modo claro')} {'✓' if self.theme_var.get() == 'Claro' else ''}", "command": lambda: self.set_theme_choice("Claro")},
            {"label": f"{self.tr('Modo escuro')} {'✓' if self.theme_var.get() == 'Escuro' else ''}", "command": lambda: self.set_theme_choice("Escuro")},
            {"separator": True},
            {"label": f"Português {'✓' if self.language_var.get() == 'Português' else ''}", "command": lambda: self.set_language_choice("Português")},
            {"label": f"English {'✓' if self.language_var.get() == 'English' else ''}", "command": lambda: self.set_language_choice("English")},
        ]

    def help_menu_items(self) -> list[dict]:
        return [
            {"label": self.tr("Leia-me"), "command": lambda: self.open_app_document("FFX Encoder GUI Leia-me.pdf", "Leia-me")},
            {"label": self.tr("Ajuda"), "command": lambda: self.open_app_document("FFX Encoder GUI Ajuda.pdf", "Ajuda")},
            {"separator": True},
            {"label": self.tr("Sobre"), "command": self.show_about},
        ]

    def set_theme_choice(self, theme: str) -> None:
        self.theme_var.set(theme)
        self.close_app_menu()
        self.apply_theme()

    def set_language_choice(self, language: str) -> None:
        self.language_var.set(language)
        self.close_app_menu()
        self.change_interface_language()

    def toggle_auto_tmdb_on_folder(self) -> None:
        self.auto_tmdb_on_folder_var.set(not self.auto_tmdb_on_folder_var.get())
        self.close_app_menu()
        self.save_gui_state()
        status = "ativada" if self.auto_tmdb_on_folder_var.get() else "desativada"
        self.status_var.set(f"Busca automática TMDb ao abrir pasta {status}.")

    def menu_palette(self) -> tuple[str, str, str, str, str]:
        if self.is_dark_theme():
            return "#202020", "#f4f4f4", "#333333", "#303030", "#4a90d9"
        return "#f0f0f0", "#202020", "#e7f1fb", "#d0d0d0", "#2f75b5"

    def style_app_menu_bar(self) -> None:
        if self.app_menu_bar is None:
            return
        bg, fg, active_bg, _border, _accent = self.menu_palette()
        self.app_menu_bar.configure(bg=bg)
        for child in self.app_menu_bar.winfo_children():
            child.configure(bg=bg, fg=fg)
            child.bind("<Enter>", lambda _event, widget=child: widget.configure(bg=active_bg), add="+")
            child.bind("<Leave>", lambda _event, widget=child, color=bg: widget.configure(bg=color), add="+")

    def close_app_menu(self, _event: tk.Event | None = None) -> None:
        if self.open_app_menu is not None:
            try:
                self.open_app_menu.destroy()
            except tk.TclError:
                pass
            self.open_app_menu = None

    def show_app_menu(self, widget: tk.Widget, items: list[dict]) -> None:
        self.close_app_menu()
        bg, fg, active_bg, border, _accent = self.menu_palette()
        menu = tk.Toplevel(self)
        self.open_app_menu = menu
        menu.overrideredirect(True)
        menu.configure(bg=border)
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height()
        menu.geometry(f"+{x}+{y}")
        inner = tk.Frame(menu, bg=bg, bd=0, highlightthickness=1, highlightbackground=border)
        inner.pack(fill=tk.BOTH, expand=True)

        for item in items:
            if item.get("separator"):
                tk.Frame(inner, height=1, bg=border).pack(fill=tk.X, padx=6, pady=4)
                continue
            command = item["command"]
            label = tk.Label(inner, text=item["label"], anchor=tk.W, bg=bg, fg=fg, padx=14, pady=6, width=28, cursor="hand2")
            label.pack(fill=tk.X)
            label.bind("<Enter>", lambda _event, w=label: w.configure(bg=active_bg), add="+")
            label.bind("<Leave>", lambda _event, w=label: w.configure(bg=bg), add="+")
            label.bind("<Button-1>", lambda _event, cmd=command: (self.close_app_menu(), cmd()), add="+")
        menu.bind("<FocusOut>", self.close_app_menu)
        menu.focus_force()

    def _add_action_tab(self, notebook: ttk.Notebook, title: str, actions: list[tuple]) -> None:
        frame = ttk.Frame(notebook, padding=4)
        notebook.add(frame, text=self.tr(title))
        for action in actions:
            text, command = action[0], action[1]
            tmdb_dependent = bool(action[2]) if len(action) > 2 else False
            button = ttk.Button(frame, text=self.tr(text), command=command)
            button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
            self.add_tooltip(button, text)
            self.action_buttons.append(button)
            if tmdb_dependent:
                self.tmdb_buttons.append(button)

    def add_tooltip(self, widget: tk.Widget, key: str) -> None:
        tips = {
            "Selecionar": "Escolhe uma pasta de trabalho para carregar os vídeos.",
            "Recarregar": "Atualiza a lista de vídeos da pasta atual.",
            "Manter/Remover": "Alterna se a faixa selecionada será mantida ou removida no arquivo de saída.",
            "Mover Acima": "Move a faixa selecionada uma posição acima na ordem final.",
            "Mover Abaixo": "Move a faixa selecionada uma posição abaixo na ordem final.",
            "Idioma": "Altera o código de idioma da faixa selecionada, como por, eng ou spa.",
            "Default": "Marca a faixa selecionada como padrão dentro do arquivo.",
            "Forced": "Liga ou desliga a flag forced na legenda selecionada.",
            "Remover Imagens": "Remove faixas de imagem/vídeo extra, como capas embutidas em formato de faixa.",
            "Remover Legendas": "Remove as legendas dos vídeos sem recodificar.",
            "Remover Anexos": "Remove anexos embutidos, preservando vídeo e áudio.",
            "Manter Tudo": "Marca todas as faixas para serem mantidas.",
            "Aplicar": "Gera um novo arquivo com as alterações feitas na lista de faixas.",
            "Áudio 1": "Mantém apenas a primeira faixa de áudio e preserva as demais faixas compatíveis.",
            "Áudio 2": "Mantém apenas a segunda faixa de áudio, se ela existir.",
            "Áudio PT": "Mantém faixas de áudio marcadas como português.",
            "Extrair Áudios": "Extrai todas as faixas de áudio dos vídeos da pasta.",
            "Extrair Áudio Opções": "Extrai áudio com escolha de faixa e formato de saída.",
            "Juntar Áudio": "Adiciona áudio externo com mesmo nome do vídeo, permitindo ajuste de idioma e atraso.",
            "Remover Legenda Nº": "Remove uma legenda específica por posição em lote.",
            "Extrair Legendas": "Extrai todas as legendas dos vídeos da pasta.",
            "Extrair Legenda Opções": "Extrai legendas escolhendo faixa, idioma ou formato.",
            "Juntar Legenda": "Adiciona legenda externa com mesmo nome do vídeo, com opção de atraso.",
            "PT+EN + Legenda PT": "Mantém áudio português e inglês, além de legendas em português.",
            "Organizar PT/EN": "Reorganiza faixas priorizando português e inglês quando disponíveis.",
            "Gerar Relatório": "Cria relatório limpo com vídeos, áudios, legendas, codecs, idiomas e flags.",
            "Verificar Vídeo": "Gera uma verificação técnica dos vídeos da pasta.",
            "Buscar Filme": "Busca o filme no TMDb antes de executar o modo inteligente de filme.",
            "Modo Inteligente Filme": "Executa a rotina inteligente para filme usando o resultado TMDb selecionado.",
            "Buscar Série": "Busca a série no TMDb antes de executar o modo inteligente de série.",
            "Modo Inteligente Série": "Converte a pasta para MKV H.265, mantém PT+EN/legenda PT e aplica capa TMDb.",
            "Buscar": "Busca capas e resultados no TMDb usando o nome digitado.",
            "Limpar": "Limpa a busca TMDb e remove a prévia carregada.",
            "Aplicar Metadados": "Aplica metadados TMDb ao filme selecionado na lista de resultados.",
            "Limpar Metadados": "Remove metadados textuais indesejados dos vídeos sem recodificar.",
            "Prévia capa": "Baixa e mostra uma prévia da capa selecionada no TMDb.",
            "Aplicar capa": "Aplica a capa selecionada aos vídeos correspondentes.",
            "Remover capa": "Remove capas e anexos de imagem embutidos dos vídeos.",
            "Cover local": "Aplica cover.jpg, cover.jpeg ou cover.png da pasta atual.",
            "Cover cache": "Procura e aplica capas salvas no cache local do FFX Encoder.",
            "Aplicar Filtro": "Aplica apenas o filtro escolhido, preservando container, codec compativel, audios, legendas e metadados sempre que possivel.",
            "Deinterlace": "Corrige vídeos entrelaçados em uma única etapa junto com resolução, denoise ou remaster.",
            "Filtro": "Escolha um filtro principal: Denoise para limpeza simples ou Remaster para limpeza com nitidez calibrada.",
            "Denoise": "Remove ruídos de imagem. Use sozinho quando quiser apenas limpar o vídeo sem aplicar nitidez de remaster.",
            "Remaster": "Aplica melhoria visual calibrada com limpeza e nitidez. Use como alternativa ao denoise simples.",
            "Remover bordas pretas": "Detecta bordas pretas com cropdetect e aplica corte somente quando o resultado parecer seguro. Experimental: confira o resultado final.",
            "Granulado leve": "Adiciona granulado discreto para reduzir aparencia plastificada apos denoise ou remaster.",
            "Granulado medio": "Adiciona granulado mais visivel, proximo de material antigo ou filmado.",
            "Granulado forte": "Adiciona granulado forte. Use com cuidado, pois pode aumentar o tamanho e dificultar compressao.",
            "Processar": "Converte os vídeos usando codec, container, áudio, qualidade, resolução, deinterlace e filtro principal. Use Vídeo copy para converter só o áudio sem recodificar imagem.",
            "Remasterizar": "Executa um remaster rápido em MKV H.265 CQ/CRF 23, com upscale opcional e áudio copy, AAC ou AAC com normalização.",
            "Remaster leve": "Remaster conservador: limpeza e nitidez sutis, indicado como ponto de partida.",
            "Remaster medio": "Remaster intermediário: melhora mais perceptível, próximo ao antigo leve, ainda com baixo risco de halos.",
            "Remaster forte": "Remaster mais intenso, recalibrado para ser menos artificial. Use em vídeos realmente fracos.",
            "Normalizar volume": "Aplica loudnorm ao áudio. Se o áudio estiver em copy, será convertido para AAC 256 kbps para permitir a normalização.",
        }
        text = tips.get(key)
        if text:
            Tooltip(widget, text)

    def show_tmdb_placeholder(self, _event: tk.Event | None = None) -> None:
        if self.tmdb_query_var.get():
            return
        self.tmdb_placeholder_active = True
        self.tmdb_query_var.set(self.tmdb_placeholder_text())
        if hasattr(self, "tmdb_entry"):
            self.tmdb_entry.configure(foreground="#8b949e" if self.is_dark_theme() else "#8a8a8a")

    def clear_tmdb_placeholder(self, _event: tk.Event | None = None) -> None:
        if self.tmdb_placeholder_active:
            self.tmdb_query_var.set("")
            self.tmdb_placeholder_active = False
            if hasattr(self, "tmdb_entry"):
                self.tmdb_entry.configure(foreground="#f0f3f6" if self.is_dark_theme() else "#202020")

    def tmdb_query_text(self) -> str:
        query = self.tmdb_query_var.get().strip()
        if self.tmdb_placeholder_active or query in {TMDB_QUERY_PLACEHOLDER_PT, TMDB_QUERY_PLACEHOLDER_EN}:
            return ""
        return query

    def tmdb_placeholder_text(self) -> str:
        return TMDB_QUERY_PLACEHOLDER_EN if self.language_var.get() == "English" else TMDB_QUERY_PLACEHOLDER_PT

    def update_conversion_recode_options(self) -> None:
        video_copy = self.codec_from_text(self.codec_var.get()) == "copy"
        if video_copy:
            self.resolution_var.set("Original")
            self.conversion_deinterlace_var.set(False)
            self.filter_var.set("None")
            self.conversion_crop_var.set(False)

        for index, widget in enumerate(self.conversion_recode_widgets):
            try:
                if index in {0, 1, 3}:
                    widget.configure(state=tk.DISABLED if video_copy else "readonly")
                else:
                    widget.configure(state=tk.DISABLED if video_copy else tk.NORMAL)
            except tk.TclError:
                pass

    def _add_conversion_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=4)
        notebook.add(frame, text=self.tr("Conversão"))
        combo_style = "Dark.TCombobox" if self.is_dark_theme() else "TCombobox"
        ttk.Label(frame, text=self.tr("Codec:")).pack(side=tk.LEFT, padx=(0, 4))
        codec_combo = ttk.Combobox(
            frame,
            textvariable=self.codec_var,
            values=("H.265 / HEVC", "H.264 / AVC", "AV1", "Vídeo copy"),
            state="readonly",
            width=14,
            style=combo_style,
        )
        codec_combo.pack(side=tk.LEFT, padx=(0, 8))
        codec_combo.bind("<<ComboboxSelected>>", lambda _event: self.update_conversion_recode_options())
        ttk.Label(frame, text=self.tr("Container:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.container_var,
            values=("MKV", "MP4"),
            state="readonly",
            width=6,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(frame, text=self.tr("Áudio:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.audio_mode_var,
            values=AUDIO_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(frame, text=self.tr("Qualidade:")).pack(side=tk.LEFT, padx=(0, 4))
        quality_combo = ttk.Combobox(
            frame,
            textvariable=self.quality_var,
            values=("CQ/CRF 23", "CQ/CRF 26", "CQ/CRF 28"),
            state="readonly",
            width=10,
            style=combo_style,
        )
        quality_combo.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(frame, text=self.tr("Resolução:")).pack(side=tk.LEFT, padx=(0, 4))
        resolution_combo = ttk.Combobox(
            frame,
            textvariable=self.resolution_var,
            values=RESOLUTION_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        )
        resolution_combo.pack(side=tk.LEFT, padx=(0, 8))
        deinterlace_check = ttk.Checkbutton(
            frame,
            text="Deinterlace",
            variable=self.conversion_deinterlace_var,
        )
        deinterlace_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(deinterlace_check, "Deinterlace")
        ttk.Label(frame, text=self.tr("Filtro:")).pack(side=tk.LEFT, padx=(0, 4))
        filter_combo = ttk.Combobox(
            frame,
            textvariable=self.filter_var,
            values=tuple(self.filter_label(value) for value in (
                "Nenhum",
                "Denoise leve",
                "Denoise medio",
                "Denoise forte",
                "Remaster leve",
                "Remaster medio",
                "Remaster forte",
            )),
            state="readonly",
            width=16,
            style=combo_style,
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(filter_combo, "Filtro")
        crop_check = ttk.Checkbutton(
            frame,
            text=self.tr("Remover bordas pretas"),
            variable=self.conversion_crop_var,
        )
        crop_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(crop_check, "Remover bordas pretas")
        self.conversion_recode_widgets = [
            quality_combo,
            resolution_combo,
            deinterlace_check,
            filter_combo,
            crop_check,
        ]
        self.update_conversion_recode_options()

        for text, command in [
            ("Processar", self.convert_batch),
        ]:
            button = ttk.Button(frame, text=self.tr(text), command=command)
            button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
            self.add_tooltip(button, text)
            self.action_buttons.append(button)

    def _add_filters_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=4)
        notebook.add(frame, text=self.tr("Filtros"))
        combo_style = "Dark.TCombobox" if self.is_dark_theme() else "TCombobox"

        ttk.Label(frame, text=self.tr("Tipo:")).pack(side=tk.LEFT, padx=(0, 4))
        filter_combo = ttk.Combobox(
            frame,
            textvariable=self.filter_only_type_var,
            values=tuple(self.filter_label(value) for value in (
                "Deinterlace",
                "Denoise leve",
                "Denoise medio",
                "Denoise forte",
                "Granulado leve",
                "Granulado medio",
                "Granulado forte",
            )),
            state="readonly",
            width=18,
            style=combo_style,
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(filter_combo, "Aplicar Filtro")

        ttk.Label(frame, text=self.tr("Ãudio:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.filter_only_audio_var,
            values=AUDIO_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Qualidade:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.filter_only_quality_var,
            values=("CQ/CRF 18", "CQ/CRF 23", "CQ/CRF 26", "CQ/CRF 28"),
            state="readonly",
            width=10,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))
        crop_check = ttk.Checkbutton(
            frame,
            text=self.tr("Remover bordas pretas"),
            variable=self.filter_only_crop_var,
        )
        crop_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(crop_check, "Remover bordas pretas")

        button = ttk.Button(frame, text=self.tr("Aplicar Filtro"), command=self.filter_only_batch)
        button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(button, "Aplicar Filtro")
        self.action_buttons.append(button)

    def _add_aspect_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=4)
        notebook.add(frame, text=self.tr("Corrigir Aspecto"))
        combo_style = "Dark.TCombobox" if self.is_dark_theme() else "TCombobox"

        ttk.Label(frame, text=self.tr("Aspecto:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.aspect_target_var,
            values=("4:3", "16:9", "21:9"),
            state="readonly",
            width=6,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Container:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.aspect_container_var,
            values=("MKV", "MP4"),
            state="readonly",
            width=6,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Áudio:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.aspect_audio_var,
            values=AUDIO_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Qualidade:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.aspect_quality_var,
            values=("CQ/CRF 18", "CQ/CRF 23", "CQ/CRF 26", "CQ/CRF 28"),
            state="readonly",
            width=10,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        copy_check = ttk.Checkbutton(
            frame,
            text=self.tr("Tentar sem recode"),
            variable=self.aspect_copy_first_var,
        )
        copy_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(copy_check, "Tentar sem recode")

        button = ttk.Button(frame, text=self.tr("Corrigir"), command=self.fix_aspect_batch)
        button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(button, "Corrigir")
        self.action_buttons.append(button)

    def _add_borders_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=4)
        notebook.add(frame, text=self.tr("Corrigir Bordas"))
        combo_style = "Dark.TCombobox" if self.is_dark_theme() else "TCombobox"

        ttk.Label(frame, text=self.tr("Modo:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.borders_mode_var,
            values=(self.tr("Automatico agressivo"), self.tr("Manual")),
            state="readonly",
            width=18,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Codec:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.borders_codec_var,
            values=("H.265 / HEVC", "H.264 / AVC", "AV1"),
            state="readonly",
            width=14,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Container:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.borders_container_var,
            values=("MKV", "MP4"),
            state="readonly",
            width=6,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Áudio:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.borders_audio_var,
            values=AUDIO_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Qualidade:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.borders_quality_var,
            values=("CQ/CRF 18", "CQ/CRF 23", "CQ/CRF 26", "CQ/CRF 28"),
            state="readonly",
            width=10,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Resolução:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.borders_resolution_var,
            values=BORDER_RESOLUTION_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Cortar:")).pack(side=tk.LEFT, padx=(0, 4))
        for label, variable in (
            ("Esq", self.borders_left_var),
            ("Dir", self.borders_right_var),
            ("Topo", self.borders_top_var),
            ("Baixo", self.borders_bottom_var),
        ):
            ttk.Label(frame, text=self.tr(label)).pack(side=tk.LEFT, padx=(0, 2))
            ttk.Entry(frame, textvariable=variable, width=4).pack(side=tk.LEFT, padx=(0, 4))

        analyze = ttk.Button(frame, text=self.tr("Analisar"), command=self.analyze_borders_batch)
        analyze.pack(side=tk.LEFT, padx=(4, 6), pady=2)
        self.add_tooltip(analyze, "Corrigir Bordas")
        self.action_buttons.append(analyze)

        button = ttk.Button(frame, text=self.tr("Corrigir"), command=self.fix_borders_batch)
        button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(button, "Corrigir Bordas")
        self.action_buttons.append(button)

    def _add_remaster_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=4)
        notebook.add(frame, text=self.tr("Remaster"))
        combo_style = "Dark.TCombobox" if self.is_dark_theme() else "TCombobox"

        self.remaster_level_var = tk.StringVar(value="Remaster leve")
        self.remaster_upscale_var = tk.StringVar(value="Original")
        self.remaster_audio_var = tk.StringVar(value="copy")

        ttk.Label(frame, text="Nível:").pack(side=tk.LEFT, padx=(0, 4))
        level = ttk.Combobox(
            frame,
            textvariable=self.remaster_level_var,
            values=("Remaster leve", "Remaster medio", "Remaster forte"),
            state="readonly",
            width=16,
            style=combo_style,
        )
        level.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(level, "Remaster leve")

        ttk.Label(frame, text=self.tr("Resolução:")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(
            frame,
            textvariable=self.remaster_upscale_var,
            values=RESOLUTION_OPTIONS,
            state="readonly",
            width=13,
            style=combo_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(frame, text=self.tr("Áudio:")).pack(side=tk.LEFT, padx=(0, 4))
        audio = ttk.Combobox(
            frame,
            textvariable=self.remaster_audio_var,
            values=REMASTER_AUDIO_OPTIONS,
            state="readonly",
            width=19,
            style=combo_style,
        )
        audio.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(audio, "Áudio")
        deinterlace_check = ttk.Checkbutton(
            frame,
            text="Deinterlace",
            variable=self.remaster_deinterlace_var,
        )
        deinterlace_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(deinterlace_check, "Deinterlace")
        normalize_check = ttk.Checkbutton(
            frame,
            text=self.tr("Normalizar volume"),
            variable=self.remaster_normalize_var,
        )
        normalize_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(normalize_check, "Normalizar volume")
        crop_check = ttk.Checkbutton(
            frame,
            text=self.tr("Remover bordas pretas"),
            variable=self.remaster_crop_var,
        )
        crop_check.pack(side=tk.LEFT, padx=(0, 8))
        self.add_tooltip(crop_check, "Remover bordas pretas")

        button = ttk.Button(frame, text=self.tr("Remasterizar"), command=self.remaster_batch)
        button.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(button, "Remasterizar")
        self.action_buttons.append(button)

    def _set_status(self) -> None:
        try:
            if not self.encoder_message:
                self.encoder_message = detect_encoder_message(self.tools)
            encoder = self.encoder_message
        except Exception:
            encoder = "Nao detectado"
        self.status_var.set(f"FFmpeg: {self.tools.ffmpeg} | Encoder: {encoder}")

    def log_line(self, text: str) -> None:
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def has_tmdb_key(self) -> bool:
        # A GUI deve liberar TMDb apenas pela chave configurada nela mesma.
        # Isso evita que tokens antigos da versao console liberem botoes por engano.
        dat_path = self.config_data.app_root / "ffx.dat"
        if dat_path.exists() and dat_path.stat().st_size > 0:
            return True

        config_paths = [
            self.config_data.app_root / "ffx.config",
            self.config_data.app_root / "tmdb.ini",
        ]
        valid_keys = ("tmdb_read_token", "read_token", "api_read_token", "token")
        for path in config_paths:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith(("#", ";")) or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                if key.strip().lower() in valid_keys and value.strip():
                    return True
        return False

    def update_tmdb_button_states(self) -> None:
        state = tk.NORMAL if self.has_tmdb_key() else tk.DISABLED
        for button in self.tmdb_buttons:
            button.configure(state=state)
        self.update_apply_metadata_button_state()

    def update_apply_metadata_button_state(self) -> None:
        button = self.apply_metadata_button
        if button is None:
            return
        enabled = (
            self.has_tmdb_key()
            and bool(self.tmdb_results)
            and bool(self.tmdb_list.curselection())
            and self.tmdb_result_mode == "metadata"
        )
        button.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def start_busy_indicator(self) -> None:
        self.busy_indicator_active = True
        self.busy_indicator_on = False
        if hasattr(self, "busy_text"):
            self.busy_text.configure(text="Processando...")
        self.pulse_busy_indicator()

    def stop_busy_indicator(self) -> None:
        self.busy_indicator_active = False
        if self.busy_indicator_after is not None:
            try:
                self.after_cancel(self.busy_indicator_after)
            except tk.TclError:
                pass
            self.busy_indicator_after = None
        if hasattr(self, "busy_canvas"):
            self.busy_canvas.itemconfigure(self.busy_dot, fill="", outline="")
        if hasattr(self, "busy_text"):
            self.busy_text.configure(text="")

    def pulse_busy_indicator(self) -> None:
        if not self.busy_indicator_active or not hasattr(self, "busy_canvas"):
            return
        self.busy_indicator_on = not self.busy_indicator_on
        color = self.busy_indicator_color if self.busy_indicator_on else self.busy_indicator_dim_color
        self.busy_canvas.itemconfigure(self.busy_dot, fill=color, outline=color)
        self.busy_indicator_after = self.after(700, self.pulse_busy_indicator)

    def set_busy(self, busy: bool, message: str | None = None) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        for button in self.action_buttons:
            button.configure(state=state)
        if not busy:
            self.update_tmdb_button_states()
        if hasattr(self, "cancel_button"):
            self.cancel_button.configure(state=tk.NORMAL if busy else tk.DISABLED)
        if hasattr(self, "open_output_button"):
            open_state = tk.NORMAL if (not busy and self.last_output_dir and self.last_output_dir.exists()) else tk.DISABLED
            self.open_output_button.configure(state=open_state)
        if busy:
            if message:
                self.status_var.set(message)
            self.start_busy_indicator()
        else:
            self.stop_busy_indicator()
            self._set_status()

    def cancel_current_process(self) -> None:
        self.cancel_event.set()
        process = self.active_process
        if process and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        self.status_var.set("Cancelando processo... aguarde.")

    def set_last_output_dir(self, folder: Path | None) -> None:
        self.last_output_dir = folder if folder and folder.exists() else None
        if hasattr(self, "open_output_button"):
            self.open_output_button.configure(state=tk.NORMAL if self.last_output_dir else tk.DISABLED)

    def open_last_output_dir(self) -> None:
        if not self.last_output_dir or not self.last_output_dir.exists():
            messagebox.showinfo("Abrir saída", "Nenhuma pasta de saída disponível ainda.")
            return
        try:
            os.startfile(self.last_output_dir)
        except OSError as exc:
            messagebox.showerror("Abrir saída", f"Não foi possível abrir a pasta:\n{exc}")

    def should_overwrite_output(self, output_path: Path) -> str:
        if not output_path.exists() or self.is_temp_output_path(output_path):
            return "yes"
        if self.overwrite_all_outputs:
            return "yes"
        if threading.current_thread() is threading.main_thread():
            return self.ask_overwrite_output(output_path)
        event = threading.Event()
        result: dict[str, str] = {}

        def ask() -> None:
            result["choice"] = self.ask_overwrite_output(output_path)
            event.set()

        self.after(0, ask)
        event.wait()
        return result.get("choice", "cancel")

    def ask_overwrite_output(self, output_path: Path) -> str:
        dialog = tk.Toplevel(self)
        dialog.title("Arquivo já existe")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        choice = {"value": "cancel"}

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="O arquivo de saída já existe:", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(frame, text=str(output_path), wraplength=620).pack(anchor=tk.W, pady=(6, 12))
        ttk.Label(frame, text="Deseja sobrescrever?").pack(anchor=tk.W, pady=(0, 10))

        buttons = ttk.Frame(frame)
        buttons.pack(anchor=tk.E)

        def set_choice(value: str) -> None:
            choice["value"] = value
            dialog.destroy()

        ttk.Button(buttons, text="Cancelar", command=lambda: set_choice("cancel")).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Não", command=lambda: set_choice("no")).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Sim para todos", command=lambda: set_choice("all")).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Sim", command=lambda: set_choice("yes")).pack(side=tk.RIGHT)
        dialog.protocol("WM_DELETE_WINDOW", lambda: set_choice("cancel"))
        dialog.wait_window()
        return choice["value"]

    def run_command(self, args: list[str | Path]) -> subprocess.CompletedProcess[str]:
        output_path = Path(args[-1]) if args else None
        if output_path and output_path.suffix:
            overwrite = self.should_overwrite_output(output_path)
            if overwrite == "cancel":
                self.cancel_event.set()
                return subprocess.CompletedProcess([str(arg) for arg in args], -999, "", "Processo cancelado pelo usuario.")
            if overwrite == "no":
                return subprocess.CompletedProcess([str(arg) for arg in args], -998, "", f"Arquivo existente ignorado: {output_path}")
            if overwrite == "all":
                self.overwrite_all_outputs = True
        startupinfo = None
        creationflags = 0
        if hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            [str(arg) for arg in args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        self.active_process = process
        try:
            while process.poll() is None:
                if self.cancel_event.is_set():
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except (OSError, subprocess.TimeoutExpired):
                        try:
                            process.kill()
                        except OSError:
                            pass
                    stdout, stderr = process.communicate()
                    return subprocess.CompletedProcess([str(arg) for arg in args], -999, stdout, stderr or "Processo cancelado pelo usuario.")
                try:
                    process.wait(timeout=0.15)
                except subprocess.TimeoutExpired:
                    continue
        finally:
            if self.active_process is process:
                self.active_process = None
        stdout, stderr = process.communicate()
        return subprocess.CompletedProcess([str(arg) for arg in args], process.returncode or 0, stdout, stderr)

    def run_background(self, message: str, task, on_done) -> None:
        self.cancel_event.clear()
        self.overwrite_all_outputs = False
        self.set_busy(True, message)
        self.log_line(message)

        def worker() -> None:
            try:
                result = task()
                self.after(0, lambda: finish(result, None))
            except Exception as exc:
                self.after(0, lambda: finish(None, exc))

        def finish(result, error) -> None:
            self.set_busy(False)
            if error:
                self.log_line(f"[ERRO] {error}")
                messagebox.showerror("Erro", str(error))
                return
            if self.cancel_event.is_set():
                self.log_line("[CANCELADO] Processo interrompido pelo usuario.")
                messagebox.showinfo("Cancelado", "Processo cancelado.")
                self.cancel_event.clear()
                return
            on_done(result)

        threading.Thread(target=worker, daemon=True).start()

    def thread_log(self, text: str) -> None:
        self.after(0, lambda: self.log_line(text))

    def thread_status(self, text: str) -> None:
        self.after(0, lambda: self.status_var.set(text))

    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=str(self.work_dir), title="Selecionar pasta de videos")
        if folder:
            self.load_folder(Path(folder))

    def choose_file(self) -> None:
        file_name = filedialog.askopenfilename(
            initialdir=str(self.work_dir),
            title="Selecionar video",
            filetypes=[("Videos", " ".join(f"*{ext}" for ext in VIDEO_EXTENSIONS)), ("Todos os arquivos", "*.*")],
        )
        if not file_name:
            return
        file_path = Path(file_name)
        self.load_folder(file_path.parent)
        try:
            index = self.video_files.index(file_path)
        except ValueError:
            return
        self.video_list.selection_clear(0, tk.END)
        self.video_list.selection_set(index)
        self.video_list.see(index)
        self.load_selected_video()

    def output_root(self) -> Path:
        custom = self.output_root_var.get().strip()
        if custom:
            return Path(custom)
        return self.work_dir / "Saida"

    def output_dir(self, *parts: str) -> Path:
        return self.output_root().joinpath(*parts)

    def temp_work_dir(self, name: str) -> Path:
        custom = self.temp_root_var.get().strip()
        if custom:
            return Path(custom) / name
        return self.output_root() / name

    def is_temp_output_path(self, path: Path) -> bool:
        if not self.temp_root_var.get().strip():
            return any(part.lower().startswith("_temp_") for part in path.parts)
        try:
            resolved = path.resolve()
            temp_root = self.temp_work_dir("").resolve()
            return resolved == temp_root or temp_root in resolved.parents
        except OSError:
            return False

    def configure_work_folders(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Pastas de trabalho")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        output_var = tk.StringVar(value=self.output_root_var.get())
        temp_var = tk.StringVar(value=self.temp_root_var.get())

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text="Deixe em branco para usar o padrão atual dentro da pasta do vídeo.",
            wraplength=520,
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))

        ttk.Label(frame, text="Pasta de saída:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=output_var, width=58).grid(row=1, column=1, sticky=tk.EW, pady=4, padx=(8, 4))
        ttk.Button(frame, text="Selecionar", command=lambda: self._choose_folder_for_var(output_var, "Selecionar pasta de saída")).grid(row=1, column=2, padx=4)
        ttk.Button(frame, text="Limpar", command=lambda: output_var.set("")).grid(row=1, column=3, padx=(4, 0))

        ttk.Label(frame, text="Pasta temporária:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(frame, textvariable=temp_var, width=58).grid(row=2, column=1, sticky=tk.EW, pady=4, padx=(8, 4))
        ttk.Button(frame, text="Selecionar", command=lambda: self._choose_folder_for_var(temp_var, "Selecionar pasta temporária")).grid(row=2, column=2, padx=4)
        ttk.Button(frame, text="Limpar", command=lambda: temp_var.set("")).grid(row=2, column=3, padx=(4, 0))

        ttk.Label(
            frame,
            text="Dica: usar discos diferentes para origem, temporário e saída pode ajudar em remuxagens e arquivos grandes.",
            wraplength=520,
        ).grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=(10, 6))

        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=4, sticky=tk.E, pady=(8, 0))

        def save() -> None:
            self.output_root_var.set(output_var.get().strip())
            self.temp_root_var.set(temp_var.get().strip())
            self.save_gui_state()
            self.log_line(f"Saída configurada: {self.output_root()}")
            self.log_line(f"Temporários configurados: {self.temp_work_dir('')}")
            dialog.destroy()

        ttk.Button(buttons, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Salvar", command=save).pack(side=tk.RIGHT)
        frame.columnconfigure(1, weight=1)
        dialog.wait_window()

    def _choose_folder_for_var(self, variable: tk.StringVar, title: str) -> None:
        folder = filedialog.askdirectory(initialdir=str(self.work_dir), title=title, parent=self)
        if folder:
            variable.set(folder)

    def configure_tmdb_key(self) -> None:
        config_path = self.config_data.app_root / "ffx.config"
        current = ""
        if config_path.exists():
            for line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip().lower().startswith(("tmdb_read_token=", "token=")):
                    current = line.split("=", 1)[1].strip()
                    break
        value = simpledialog.askstring("Chave TMDb", "Token de leitura TMDb:", initialvalue=current, show="*")
        if not value:
            return
        config_path.write_text(f"tmdb_read_token={value.strip()}\n", encoding="utf-8")
        self.update_tmdb_button_states()
        messagebox.showinfo("Chave TMDb", f"Token salvo em:\n{config_path}")

    def open_app_document(self, filename: str, title: str) -> None:
        candidates = [
            self.config_data.app_root / filename,
            Path(__file__).resolve().parent / filename,
        ]
        for path in candidates:
            if path.exists():
                try:
                    os.startfile(path)
                    return
                except OSError as exc:
                    messagebox.showerror(title, f"Nao foi possivel abrir:\n{path}\n\n{exc}")
                    return
        messagebox.showwarning(title, f"Arquivo nao encontrado:\n{filename}")

    def show_about(self) -> None:
        open_terms = messagebox.askyesno(
            "Sobre",
            f"FFX Encoder GUI {GUI_VERSION}\n\n"
            "Ferramenta grafica para organizacao, conversao e padronizacao de arquivos de video com FFmpeg integrado.\n\n"
            "Inclui rotinas para audios, legendas, capas, metadados, relatorios, conversao e modos inteligentes para filmes e series.\n\n"
            "O uso deve respeitar o termo de responsabilidade instalado junto ao programa.\n\n"
            "Deseja abrir o termo de responsabilidade agora?",
        )
        if open_terms:
            self.open_app_document("FFX Encoder GUI Termo de Responsabilidade.pdf", "Termo de responsabilidade")

    def is_dark_theme(self) -> bool:
        return self.theme_var.get() == "Escuro"

    def change_interface_language(self) -> None:
        self.save_gui_state()
        if hasattr(self, "tmdb_entry") and self.tmdb_placeholder_active:
            self.tmdb_query_var.set("")
            self.show_tmdb_placeholder()
        messagebox.showinfo(
            "Idioma",
            "O idioma foi salvo. Feche e abra o FFX Encoder GUI para recarregar todos os textos da interface.",
        )

    def apply_theme(self) -> None:
        dark = self.is_dark_theme()
        self.save_gui_state()
        self.style_app_menu_bar()
        self.close_app_menu()
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        if dark:
            bg = "#202020"
            panel = "#242424"
            panel2 = "#2b2b2b"
            fg = "#f4f4f4"
            muted = "#dcdcdc"
            accent = "#4a90d9"
            active = "#333333"
            pressed = "#181818"
            field = "#1f1f1f"
            select = "#315f8f"
            border = "#3d3d3d"
            border_soft = "#303030"
            trough = "#171717"
            scrollbar = "#2d2d2d"
        else:
            bg = "#f0f0f0"
            panel = "#f7f7f7"
            panel2 = "#ffffff"
            fg = "#202020"
            muted = "#404040"
            accent = "#2f75b5"
            active = "#e7f1fb"
            pressed = "#e5e5e5"
            field = "#ffffff"
            select = "#cce5ff"
            border = "#d0d0d0"
            border_soft = border
            trough = panel
            scrollbar = "#e5e5e5"

        self.configure(bg=bg)
        style.configure(".", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=panel, foreground=fg, bordercolor=border_soft, lightcolor=border_soft, darkcolor=border_soft, relief="solid")
        style.configure("TLabelframe.Label", background=panel, foreground=fg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=panel2, foreground=fg, bordercolor=border, lightcolor=border_soft, darkcolor=border_soft, focusthickness=1, focuscolor=border_soft)
        style.map(
            "TButton",
            background=[("active", active), ("pressed", pressed), ("disabled", panel)],
            foreground=[("disabled", "#8f8f8f" if dark else "#909090")],
        )
        style.configure(
            "TCheckbutton",
            background=bg,
            foreground=fg,
            indicatorbackground=field,
            indicatorforeground=fg,
            bordercolor=border,
            lightcolor=border_soft,
            darkcolor=border_soft,
            focuscolor=border_soft,
        )
        style.map(
            "TCheckbutton",
            background=[("active", active), ("pressed", pressed), ("disabled", bg)],
            foreground=[("active", fg), ("pressed", fg), ("disabled", "#8f8f8f" if dark else "#909090")],
            indicatorbackground=[("selected", field), ("active", field), ("pressed", field), ("disabled", panel)],
            indicatorforeground=[("selected", fg), ("active", fg), ("pressed", fg), ("disabled", "#8f8f8f" if dark else "#909090")],
        )
        style.configure("TEntry", fieldbackground=field, foreground=fg, insertcolor=fg, bordercolor=border, lightcolor=border, darkcolor=border_soft)
        for combo_style in ("TCombobox", "Dark.TCombobox"):
            style.configure(
                combo_style,
                fieldbackground=field,
                background=panel2,
                foreground=fg,
                selectbackground=field,
                selectforeground=fg,
                arrowcolor=muted,
                bordercolor=border,
                lightcolor=border_soft,
                darkcolor=border_soft,
                insertcolor=fg,
            )
            style.map(
                combo_style,
                fieldbackground=[("readonly", field), ("disabled", panel)],
                foreground=[("readonly", fg), ("disabled", "#8f8f8f" if dark else "#909090")],
                background=[("readonly", panel2), ("active", active), ("pressed", pressed)],
                selectbackground=[("readonly", field)],
                selectforeground=[("readonly", fg)],
            )
        self.option_add("*TCombobox*Listbox.background", field)
        self.option_add("*TCombobox*Listbox.foreground", fg)
        self.option_add("*TCombobox*Listbox.selectBackground", select)
        self.option_add("*TCombobox*Listbox.selectForeground", fg)
        style.configure("TNotebook", background=panel, bordercolor=border_soft, lightcolor=border_soft, darkcolor=border_soft)
        style.configure("TNotebook.Tab", background=panel, foreground=fg, bordercolor=border_soft, lightcolor=border_soft, darkcolor=border_soft, focuscolor=panel)
        style.map(
            "TNotebook.Tab",
            background=[("selected", panel2), ("active", active)],
            foreground=[("selected", fg), ("active", fg)],
            lightcolor=[("selected", border_soft), ("active", border_soft)],
            bordercolor=[("selected", border_soft), ("active", border_soft)],
        )
        style.configure("Treeview", background=field, fieldbackground=field, foreground=fg, bordercolor=border_soft, lightcolor=border_soft, darkcolor=border_soft, rowheight=24)
        style.map("Treeview", background=[("selected", select)], foreground=[("selected", fg)])
        style.configure("Treeview.Heading", background=panel2, foreground=fg, bordercolor=border_soft, lightcolor=border_soft, darkcolor=border_soft, relief="flat")
        style.configure("Vertical.TScrollbar", background=scrollbar, troughcolor=field, bordercolor=border_soft, arrowcolor=fg, lightcolor=border_soft, darkcolor=border_soft)
        style.map("Vertical.TScrollbar", background=[("active", active), ("pressed", pressed)])
        style.configure("Horizontal.TScrollbar", background=scrollbar, troughcolor=field, bordercolor=border_soft, arrowcolor=fg, lightcolor=border_soft, darkcolor=border_soft)
        style.map("Horizontal.TScrollbar", background=[("active", active), ("pressed", pressed)])
        style.configure("Horizontal.TProgressbar", troughcolor=trough, background=accent)

        if hasattr(self, "video_list"):
            self.video_list.configure(bg=field, fg=fg, selectbackground=select, selectforeground=fg, highlightbackground=border_soft, highlightcolor=border_soft, relief=tk.FLAT)
        if hasattr(self, "tmdb_list"):
            self.tmdb_list.configure(bg=field, fg=fg, selectbackground=select, selectforeground=fg, highlightbackground=border_soft, highlightcolor=border_soft, relief=tk.FLAT)
        if hasattr(self, "log"):
            self.log.configure(bg=field, fg=muted if dark else fg, insertbackground=fg, highlightbackground=border_soft, highlightcolor=border_soft, relief=tk.FLAT)
        if hasattr(self, "busy_canvas"):
            self.busy_indicator_color = "#4aa3ff" if dark else "#2f75b5"
            self.busy_indicator_dim_color = "#284766" if dark else "#9bbbd8"
            self.busy_canvas.configure(bg=bg)
        if hasattr(self, "tmdb_entry"):
            if self.tmdb_placeholder_active:
                self.tmdb_entry.configure(foreground="#8b949e" if dark else "#9a9a9a")
            else:
                self.tmdb_entry.configure(foreground=fg)

    def load_folder(self, folder: Path) -> None:
        if not folder.exists():
            messagebox.showerror("Pasta invalida", "A pasta selecionada nao existe.")
            return
        self.work_dir = folder
        self.folder_var.set(str(folder))
        self.video_files = sorted(file for file in folder.iterdir() if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS)
        self.video_list.delete(0, tk.END)
        for file in self.video_files:
            self.video_list.insert(tk.END, file.name)
        self.tracks = []
        self.current_file = None
        self.refresh_tree()
        self.log_line(f"Pasta carregada: {folder}")
        self.after(350, self.auto_tmdb_lookup_for_folder)

    def load_selected_video(self) -> None:
        selection = self.video_list.curselection()
        if not selection:
            return
        self.current_file = self.video_files[selection[0]]
        self.tracks = self.build_tracks(self.current_file)
        self.refresh_tree()
        self.log_line(f"Video carregado: {self.current_file.name}")

    def build_tracks(self, file_path: Path) -> list[dict]:
        counters = {"v": 0, "a": 0, "s": 0, "t": 0, "d": 0}
        labels = {"v": "Video", "a": "Audio", "s": "Legenda", "t": "Anexo", "d": "Dados"}
        tracks = []
        for stream in ffprobe_streams(self.tools, file_path):
            codec_type = str(stream.get("codec_type", "data")).lower()
            track_type = {
                "video": "v",
                "audio": "a",
                "subtitle": "s",
                "attachment": "t",
                "data": "d",
            }.get(codec_type, "d")
            counters[track_type] += 1
            tracks.append({
                "keep": True,
                "source_index": int(stream.get("index", 0)),
                "type": track_type,
                "relative": counters[track_type] - 1,
                "label": f"{labels[track_type]} {counters[track_type]}",
                "codec": str(stream.get("codec_name", "desconhecido")),
                "language": stream_language(stream),
                "title": stream_title(stream),
                "default": disposition(stream, "default") if track_type in {"a", "s"} else False,
                "forced": disposition(stream, "forced") if track_type == "s" else False,
                "hearing_impaired": disposition(stream, "hearing_impaired") if track_type in {"a", "s"} else False,
            })
        return tracks

    def refresh_labels(self) -> None:
        counters = {"v": 0, "a": 0, "s": 0, "t": 0, "d": 0}
        labels = {"v": "Video", "a": "Audio", "s": "Legenda", "t": "Anexo", "d": "Dados"}
        for track in self.tracks:
            counters[track["type"]] += 1
            track["relative"] = counters[track["type"]] - 1
            track["label"] = f"{labels[track['type']]} {counters[track['type']]}"

    def refresh_tree(self) -> None:
        selected_source_indexes = {self.tracks[int(item)]["source_index"] for item in self.tree.selection() if item.isdigit() and int(item) < len(self.tracks)}
        self.tree.delete(*self.tree.get_children())
        for index, track in enumerate(self.tracks):
            flags = []
            if track["default"]:
                flags.append("default")
            if track["forced"]:
                flags.append("forced")
            if track["hearing_impaired"]:
                flags.append("hearing_impaired")
            values = (
                "manter" if track["keep"] else "remover",
                track["label"],
                track["codec"],
                track["language"] if track["type"] in {"a", "s"} else "",
                ", ".join(flags),
                track["title"],
            )
            self.tree.insert("", tk.END, iid=str(index), values=values)
        for index, track in enumerate(self.tracks):
            if track["source_index"] in selected_source_indexes:
                self.tree.selection_add(str(index))

    def selected_indexes(self) -> list[int]:
        return sorted(int(item) for item in self.tree.selection() if item.isdigit())

    def selected_tracks(self) -> list[dict]:
        return [self.tracks[index] for index in self.selected_indexes()]

    def toggle_selected(self) -> None:
        for track in self.selected_tracks():
            track["keep"] = not track["keep"]
        self.refresh_tree()

    def move_selected(self, direction: int) -> None:
        indexes = self.selected_indexes()
        if len(indexes) != 1:
            messagebox.showinfo("Mover faixa", "Selecione apenas uma faixa para mover.")
            return
        selected = self.tracks[indexes[0]]
        same_type_positions = [idx for idx, track in enumerate(self.tracks) if track["type"] == selected["type"]]
        current_type_pos = same_type_positions.index(indexes[0])
        new_type_pos = current_type_pos + direction
        if new_type_pos < 0 or new_type_pos >= len(same_type_positions):
            return
        target = same_type_positions[new_type_pos]
        self.tracks[indexes[0]], self.tracks[target] = self.tracks[target], self.tracks[indexes[0]]
        self.refresh_labels()
        self.refresh_tree()
        self.tree.selection_set(str(target))

    def change_language(self) -> None:
        tracks = [track for track in self.selected_tracks() if track["type"] in {"a", "s"}]
        if not tracks:
            messagebox.showinfo("Idioma", "Selecione uma ou mais faixas de audio/legenda.")
            return
        value = simpledialog.askstring("Idioma", "Codigo de idioma (ex: por, eng, spa, und):", initialvalue=tracks[0]["language"])
        if not value:
            return
        value = value.strip().lower()[:3]
        for track in tracks:
            track["language"] = value
        self.refresh_tree()

    def set_default(self) -> None:
        indexes = self.selected_indexes()
        if len(indexes) != 1:
            messagebox.showinfo("Default", "Selecione uma faixa de audio ou legenda.")
            return
        selected = self.tracks[indexes[0]]
        if selected["type"] not in {"a", "s"}:
            return
        for track in self.tracks:
            if track["type"] == selected["type"]:
                track["default"] = False
        selected["default"] = True
        self.refresh_tree()

    def toggle_forced(self) -> None:
        for track in self.selected_tracks():
            if track["type"] == "s":
                track["forced"] = not track["forced"]
        self.refresh_tree()

    def remove_image_videos(self) -> None:
        video_position = 0
        changed = False
        for track in self.tracks:
            if track["type"] == "v":
                video_position += 1
                if video_position > 1 and (track["codec"].lower() in IMAGE_VIDEO_CODECS or "cover" in track["title"].lower() or "image/" in track["title"].lower()):
                    track["keep"] = False
                    changed = True
        if not changed:
            messagebox.showinfo("Remover imagens", "Nenhuma imagem em faixa de video foi encontrada.")
        self.refresh_tree()

    def remove_subtitles(self) -> None:
        for track in self.tracks:
            if track["type"] == "s":
                track["keep"] = False
        self.refresh_tree()

    def remove_attachments(self) -> None:
        for track in self.tracks:
            if track["type"] == "t":
                track["keep"] = False
        self.refresh_tree()

    def keep_all(self) -> None:
        for track in self.tracks:
            track["keep"] = True
        self.refresh_tree()

    def apply_changes(self) -> None:
        if not self.current_file:
            return
        kept = [track for track in self.tracks if track["keep"]]
        removed = [track for track in self.tracks if not track["keep"]]
        if not kept:
            messagebox.showwarning("Aplicar", "Nenhuma faixa marcada para manter.")
            return
        if not any(track["type"] == "v" for track in kept):
            messagebox.showwarning("Aplicar", "Pelo menos uma faixa de video precisa ser mantida.")
            return

        out_dir = self.output_dir("Audio", "Editor_Faixas_GUI")
        out_file = out_dir / f"{self.current_file.stem}.mkv"
        summary = [
            "SERA MANTIDO:",
            *[f"- {track['label']} - {track['codec']} - {track['language'] if track['type'] in {'a', 's'} else ''} {track['title']}".strip() for track in kept],
            "",
            "SERA REMOVIDO:",
            *([f"- {track['label']} - {track['codec']} - {track['language'] if track['type'] in {'a', 's'} else ''} {track['title']}".strip() for track in removed] or ["- Nada"]),
            "",
            f"Saida: {out_file}",
            "",
            "Confirmar e aplicar?",
        ]
        if not messagebox.askyesno("Resumo antes de aplicar", "\n".join(summary)):
            return
        if out_file.exists() and not messagebox.askyesno("Arquivo existente", "Arquivo de saida ja existe. Sobrescrever?"):
            return

        ensure_dir(out_dir)
        args: list[str | Path] = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", self.current_file]
        for track in kept:
            args.extend(["-map", f"0:{track['source_index']}"])
        args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", "-disposition:a", "0", "-disposition:s", "0"])

        output_relative = {"a": 0, "s": 0}
        for track in kept:
            if track["type"] not in {"a", "s"}:
                continue
            relative = output_relative[track["type"]]
            output_relative[track["type"]] += 1
            args.extend([f"-metadata:s:{track['type']}:{relative}", f"language={track['language']}"])
            flags = []
            if track["default"]:
                flags.append("default")
            if track["forced"]:
                flags.append("forced")
            if track["hearing_impaired"]:
                flags.append("hearing_impaired")
            if flags:
                args.extend([f"-disposition:{track['type']}:{relative}", "+".join(flags)])
        args.append(out_file)

        def task() -> subprocess.CompletedProcess[str]:
            return self.run_command(args)

        def done(result: subprocess.CompletedProcess[str]) -> None:
            if result.returncode == 0:
                self.set_last_output_dir(out_dir)
                self.log_line(f"Concluido: {out_file}")
                messagebox.showinfo("Concluido", f"Arquivo salvo em:\n{out_file}")
            else:
                self.log_line(result.stderr.strip() or "Erro desconhecido.")
                messagebox.showerror("Erro", result.stderr.strip() or "Erro ao aplicar alteracoes.")

        self.run_background(f"Processando {self.current_file.name}... aguarde.", task, done)

    def video_files_in_folder(self) -> list[Path]:
        return sorted(file for file in self.work_dir.iterdir() if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS)

    def generate_report(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Relatorio", "Nenhum video encontrado.")
            return
        out_dir = self.output_dir("Relatorios")
        ensure_dir(out_dir)
        out_file = out_dir / "relatorio_faixas_gui.txt"
        lines = ["RELATORIO DE FAIXAS", f"Pasta: {self.work_dir}", ""]
        for video in videos:
            lines.extend(["=========================================================", video.name, "========================================================="])
            tracks = self.build_tracks(video)
            media_tracks = [track for track in tracks if track["type"] in {"a", "s"}]
            if not media_tracks:
                lines.append("audio/legenda: nenhuma")
            for track in media_tracks:
                flags = []
                if track["default"]:
                    flags.append("default")
                if track["forced"]:
                    flags.append("forced")
                if track["hearing_impaired"]:
                    flags.append("hearing_impaired")
                flag_text = f" {' '.join(flags)}" if flags else ""
                lines.append(f"{track['label'].lower()} ({track['language']}) {track['codec']}{flag_text}")
            lines.append("")
        out_file.write_text("\n".join(lines), encoding="utf-8")
        self.log_line(f"Relatorio salvo: {out_file}")
        messagebox.showinfo("Relatorio", f"Relatorio salvo em:\n{out_file}")

    def generate_video_check_report(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Verificar video", "Nenhum video encontrado.")
            return
        out_dir = self.output_dir("Relatorios")
        ensure_dir(out_dir)
        out_file = out_dir / "relatorio_video_gui.txt"

        def task() -> tuple[int, list[str]]:
            lines = ["RELATORIO DE VIDEO", f"Pasta: {self.work_dir}", ""]
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"Verificando video ({index}/{len(videos)}): {video.name}")
                tracks = self.build_tracks(video)
                video_tracks = [track for track in tracks if track["type"] == "v"]
                main_video = video_tracks[0] if video_tracks else None
                resolution = "desconhecida"
                fps = ""
                scan_hint = "nao verificado"
                probe = run_hidden([
                    self.tools.ffprobe,
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height,avg_frame_rate,field_order",
                    "-of",
                    "json",
                    video,
                ])
                if probe.returncode == 0 and probe.stdout.strip():
                    try:
                        data = json.loads(probe.stdout)
                        stream = (data.get("streams") or [{}])[0]
                        width = stream.get("width") or "?"
                        height = stream.get("height") or "?"
                        resolution = f"{width}x{height}"
                        fps = str(stream.get("avg_frame_rate") or "")
                        field_order = str(stream.get("field_order") or "unknown")
                        if field_order and field_order != "unknown":
                            scan_hint = field_order
                    except (json.JSONDecodeError, IndexError, TypeError):
                        pass
                lines.extend([
                    "=========================================================",
                    video.name,
                    "=========================================================",
                    f"video: {main_video['codec'] if main_video else 'desconhecido'} {resolution} {fps}".strip(),
                    f"scan/interlace: {scan_hint}",
                    f"audios: {len([track for track in tracks if track['type'] == 'a'])}",
                    f"legendas: {len([track for track in tracks if track['type'] == 's'])}",
                    f"anexos: {len([track for track in tracks if track['type'] == 't'])}",
                    "",
                ])
            out_file.write_text("\n".join(lines), encoding="utf-8")
            return len(videos), [f"[OK] Relatorio de video salvo: {out_file}"]

        def done(result: tuple[int, list[str]]) -> None:
            _count, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Verificar video", f"Relatorio salvo em:\n{out_file}")

        self.run_background("Verificando videos... aguarde.", task, done)

    def copy_tracks_batch(self, title: str, folder: str, label: str, track_selector) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo(title, "Nenhum video encontrado.")
            return
        if not messagebox.askyesno(title, f"{title} em todos os videos da pasta?"):
            return
        out_dir = self.output_dir("Audio", folder)
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                tracks = self.build_tracks(video)
                kept = track_selector(tracks)
                kept_ids = {id(track) for track in kept}
                removed = [track for track in tracks if id(track) not in kept_ids]
                if not removed:
                    logs.append(f"[PULADO] {video.name} - nada para remover/organizar")
                    continue
                if not any(track["type"] == "v" for track in kept):
                    logs.append(f"[PULADO] {video.name} - resultado ficaria sem video")
                    continue
                self.thread_status(f"{title} ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[{label}] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args: list[str | Path] = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video]
                for track in kept:
                    args.extend(["-map", f"0:{track['source_index']}"])
                args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", "-disposition:a", "0", "-disposition:s", "0"])
                output_relative = {"a": 0, "s": 0}
                for track in kept:
                    if track["type"] not in {"a", "s"}:
                        continue
                    relative = output_relative[track["type"]]
                    output_relative[track["type"]] += 1
                    args.extend([f"-metadata:s:{track['type']}:{relative}", f"language={track['language']}"])
                    flags = []
                    if track["type"] == "a" and relative == 0:
                        flags.append("default")
                    elif track["type"] == "s" and track["default"]:
                        flags.append("default")
                    if track["type"] == "s" and track["forced"]:
                        flags.append("forced")
                    if track["hearing_impaired"]:
                        flags.append("hearing_impaired")
                    if flags:
                        args.extend([f"-disposition:{track['type']}:{relative}", "+".join(flags)])
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] {title}: {out_file}")
                elif result.returncode == -999:
                    break
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo(title, f"Processo concluido. Arquivos OK: {ok}")

        self.run_background(f"{title}... aguarde.", task, done)

    def remove_image_videos_batch(self) -> None:
        def selector(tracks: list[dict]) -> list[dict]:
            kept = []
            for track in tracks:
                remove = False
                if track["type"] == "v" and track["relative"] > 0:
                    title = track["title"].lower()
                    codec = track["codec"].lower()
                    remove = codec in IMAGE_VIDEO_CODECS or "cover" in title or "image/" in title
                if not remove:
                    kept.append(track)
            return kept

        self.copy_tracks_batch("Remover imagens extras", "Sem_Imagens_GUI", "REMOVER IMAGENS", selector)

    def remove_attachments_batch(self) -> None:
        self.copy_tracks_batch(
            "Remover anexos",
            "Sem_Anexos_GUI",
            "REMOVER ANEXOS",
            lambda tracks: [track for track in tracks if track["type"] != "t"],
        )

    def organize_pt_en_batch(self) -> None:
        def selector(tracks: list[dict]) -> list[dict]:
            videos = [track for track in tracks if track["type"] == "v"]
            audios = [track for track in tracks if track["type"] == "a"]
            subs = [track for track in tracks if track["type"] == "s"]
            others = [track for track in tracks if track["type"] in {"t", "d"}]
            ordered_audio = [track for track in audios if track["language"] == "por"]
            ordered_audio += [track for track in audios if track["language"] in {"eng", "en"}]
            ordered_audio += [track for track in audios if track not in ordered_audio]
            ordered_subs = [track for track in subs if track["language"] == "por"]
            ordered_subs += [track for track in subs if track not in ordered_subs]
            return [*videos, *ordered_audio, *ordered_subs, *others]

        self.copy_tracks_batch("Organizar faixas PT/EN", "Organizar_PT_EN_GUI", "ORGANIZAR PT/EN", selector)

    def _preset_tracks(self, video: Path, preset: str) -> tuple[list[dict], str]:
        tracks = self.build_tracks(video)
        video_tracks = [track for track in tracks if track["type"] == "v"]
        audio_tracks = [track for track in tracks if track["type"] == "a"]
        subtitle_tracks = [track for track in tracks if track["type"] == "s"]
        other_tracks = [track for track in tracks if track["type"] in {"t", "d"}]

        if preset == "audio1":
            selected_audio = audio_tracks[:1]
            label = "AUDIO 1"
        elif preset == "audio2":
            selected_audio = audio_tracks[1:2]
            label = "AUDIO 2"
        elif preset == "audio_pt":
            selected_audio = [track for track in audio_tracks if track["language"] == "por"]
            label = "AUDIO PT"
        elif preset == "pt_en_sub_pt":
            selected_audio = [track for track in audio_tracks if track["language"] == "por"]
            selected_audio += [track for track in audio_tracks if track["language"] in {"eng", "en"}]
            subtitle_tracks = [track for track in subtitle_tracks if track["language"] == "por"]
            label = "PT+EN"
        elif preset == "remove_subtitles":
            selected_audio = audio_tracks
            subtitle_tracks = []
            label = "REMOVER LEGENDAS"
        else:
            selected_audio = audio_tracks
            label = "PRESET"

        return [*video_tracks, *selected_audio, *subtitle_tracks, *other_tracks], label

    def keep_tracks_preset_batch(self, preset: str) -> None:
        names = {
            "audio1": ("Manter apenas áudio 1", "Audio_1_GUI"),
            "audio2": ("Manter apenas áudio 2", "Audio_2_GUI"),
            "audio_pt": ("Manter apenas áudio PT", "Audio_PT_GUI"),
            "pt_en_sub_pt": ("Manter PT+EN e legenda PT", "PT_EN_Legenda_PT_GUI"),
            "remove_subtitles": ("Remover legendas", "Sem_Legendas_GUI"),
        }
        title, folder = names.get(preset, ("Processar faixas", "Faixas_GUI"))
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo(title, "Nenhum video encontrado.")
            return
        if not messagebox.askyesno(title, f"{title} em todos os videos da pasta?"):
            return
        out_dir = self.output_dir("Audio", folder)
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                kept, label = self._preset_tracks(video, preset)
                if not kept or not any(track["type"] == "v" for track in kept):
                    logs.append(f"[PULADO] {video.name} - sem faixa de video")
                    continue
                if preset != "remove_subtitles" and not any(track["type"] == "a" for track in kept):
                    logs.append(f"[PULADO] {video.name} - faixa de audio solicitada nao encontrada")
                    continue
                self.thread_status(f"{title} ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[{label}] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args: list[str | Path] = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video]
                for track in kept:
                    args.extend(["-map", f"0:{track['source_index']}"])
                args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", "-disposition:a", "0", "-disposition:s", "0"])

                output_relative = {"a": 0, "s": 0}
                first_audio_done = False
                for track in kept:
                    if track["type"] not in {"a", "s"}:
                        continue
                    relative = output_relative[track["type"]]
                    output_relative[track["type"]] += 1
                    args.extend([f"-metadata:s:{track['type']}:{relative}", f"language={track['language']}"])
                    flags = []
                    if track["type"] == "a" and not first_audio_done:
                        flags.append("default")
                        first_audio_done = True
                    elif track["type"] == "s" and track["default"]:
                        flags.append("default")
                    if track["type"] == "s" and track["forced"]:
                        flags.append("forced")
                    if track["hearing_impaired"]:
                        flags.append("hearing_impaired")
                    if flags:
                        args.extend([f"-disposition:{track['type']}:{relative}", "+".join(flags)])
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] {title}: {out_file}")
                elif result.returncode == -999:
                    break
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo(title, f"Processo concluido. Arquivos OK: {ok}")

        self.run_background(f"{title}... aguarde.", task, done)

    def remove_subtitles_batch(self) -> None:
        self.keep_tracks_preset_batch("remove_subtitles")

    def remove_subtitle_position_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Remover legenda", "Nenhum video encontrado.")
            return
        raw = simpledialog.askinteger("Remover legenda", "Numero da legenda para remover em todos os videos:", minvalue=1)
        if not raw:
            return
        position = int(raw)
        if not messagebox.askyesno("Remover legenda", f"Remover a legenda {position} de todos os videos que tiverem essa faixa?"):
            return
        out_dir = self.output_dir("Legendas", f"Sem_Legenda_{position}_GUI")
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                tracks = self.build_tracks(video)
                subtitles = [track for track in tracks if track["type"] == "s"]
                if len(subtitles) < position:
                    logs.append(f"[PULADO] {video.name} - nao possui legenda {position}")
                    continue
                remove_source = subtitles[position - 1]["source_index"]
                self.thread_status(f"Removendo legenda {position} ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[REMOVER LEGENDA {position}] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args: list[str | Path] = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video]
                for track in tracks:
                    if track["source_index"] != remove_source:
                        args.extend(["-map", f"0:{track['source_index']}"])
                args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", out_file])
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Legenda {position} removida: {out_file}")
                elif result.returncode == -999:
                    break
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Remover legenda", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background(f"Removendo legenda {position}... aguarde.", task, done)

    def extract_audio_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Extrair audios", "Nenhum video encontrado.")
            return
        if not messagebox.askyesno("Extrair audios", "Extrair todas as faixas de audio dos videos da pasta?"):
            return
        out_dir = self.output_dir("Audio", "Extraidos_GUI")
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for video_index, video in enumerate(videos, start=1):
                self.thread_status(f"Extraindo audios ({video_index}/{len(videos)}): {video.name}")
                audio_tracks = [track for track in self.build_tracks(video) if track["type"] == "a"]
                if not audio_tracks:
                    logs.append(f"[PULADO] {video.name} - sem audio")
                    continue
                for number, track in enumerate(audio_tracks, start=1):
                    self.thread_log(f"[AUDIO] {video.name} - faixa {number}")
                    extension = audio_extension(track["codec"])
                    language = track["language"] or "und"
                    out_file = out_dir / f"{video.stem}_audio{number}_{language}{extension}"
                    args = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video, "-map", f"0:{track['source_index']}", "-c", "copy", out_file]
                    result = self.run_command(args)
                    if result.returncode == 0:
                        ok += 1
                        logs.append(f"[OK] Audio extraido: {out_file}")
                    else:
                        logs.append(f"[ERRO] {video.name} audio {number}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Extrair audios", f"Processo concluido. Faixas extraidas: {ok}")

        self.run_background("Extraindo audios... aguarde.", task, done)

    def extract_audio_options_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Extrair audio", "Nenhum video encontrado.")
            return
        selector = simpledialog.askstring(
            "Extrair audio",
            "Faixa para extrair: 1, 2, pt ou todos",
            initialvalue="1",
        )
        if not selector:
            return
        selector = selector.strip().lower()
        output_format = simpledialog.askstring(
            "Formato do audio",
            "Formato: original, aac ou mp3",
            initialvalue="original",
        )
        if not output_format:
            return
        output_format = output_format.strip().lower()
        if output_format not in {"original", "aac", "mp3"}:
            messagebox.showwarning("Formato do audio", "Use: original, aac ou mp3.")
            return

        out_dir = self.output_dir("Audio", "Extraidos_Opcoes_GUI")
        ensure_dir(out_dir)

        def chosen_tracks(video: Path) -> list[dict]:
            audios = [track for track in self.build_tracks(video) if track["type"] == "a"]
            if selector in {"todos", "all"}:
                return audios
            if selector in {"pt", "por"}:
                return [track for track in audios if track["language"] == "por"]
            if selector.isdigit():
                index = int(selector) - 1
                return audios[index:index + 1]
            return []

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for video_index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                tracks = chosen_tracks(video)
                if not tracks:
                    logs.append(f"[PULADO] {video.name} - audio solicitado nao encontrado")
                    continue
                self.thread_status(f"Extraindo audio ({video_index}/{len(videos)}): {video.name}")
                for number, track in enumerate(tracks, start=1):
                    language = track["language"] or "und"
                    if output_format == "aac":
                        extension = ".m4a"
                        codec_args = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
                    elif output_format == "mp3":
                        extension = ".mp3"
                        codec_args = ["-c:a", "libmp3lame", "-b:a", "320k"]
                    else:
                        extension = audio_extension(track["codec"])
                        codec_args = ["-c", "copy"]
                    suffix = selector if selector not in {"todos", "all"} else f"audio{number}"
                    out_file = out_dir / f"{video.stem}_{suffix}_{language}{extension}"
                    self.thread_log(f"[AUDIO {suffix.upper()}] {video.name}")
                    args = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video, "-map", f"0:{track['source_index']}", *codec_args, out_file]
                    result = self.run_command(args)
                    if result.returncode == 0:
                        ok += 1
                        logs.append(f"[OK] Audio extraido: {out_file}")
                    elif result.returncode == -999:
                        return ok, logs
                    else:
                        logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Extrair audio", f"Processo concluido. Faixas extraidas: {ok}")

        self.run_background("Extraindo audio com opcoes... aguarde.", task, done)

    def extract_subtitles_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Extrair legendas", "Nenhum video encontrado.")
            return
        if not messagebox.askyesno("Extrair legendas", "Extrair todas as legendas dos videos da pasta?"):
            return
        out_dir = self.output_dir("Legendas", "Extraidas_GUI")
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for video_index, video in enumerate(videos, start=1):
                self.thread_status(f"Extraindo legendas ({video_index}/{len(videos)}): {video.name}")
                subtitles = [track for track in self.build_tracks(video) if track["type"] == "s"]
                if not subtitles:
                    logs.append(f"[PULADO] {video.name} - sem legenda")
                    continue
                for number, track in enumerate(subtitles, start=1):
                    self.thread_log(f"[LEGENDA] {video.name} - faixa {number}")
                    extension = subtitle_extension(track["codec"])
                    language = track["language"] or "und"
                    out_file = out_dir / f"{video.stem}_legenda{number}_{language}{extension}"
                    codec_args: list[str | Path] = ["-c", "copy"]
                    if extension == ".srt" and track["codec"].lower() not in {"subrip"}:
                        codec_args = ["-c:s", "srt"]
                    args = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video, "-map", f"0:{track['source_index']}", *codec_args, out_file]
                    result = self.run_command(args)
                    if result.returncode == 0:
                        ok += 1
                        logs.append(f"[OK] Legenda extraida: {out_file}")
                    else:
                        logs.append(f"[ERRO] {video.name} legenda {number}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Extrair legendas", f"Processo concluido. Legendas extraidas: {ok}")

        self.run_background("Extraindo legendas... aguarde.", task, done)

    def extract_subtitle_options_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Extrair legenda", "Nenhum video encontrado.")
            return
        selector = simpledialog.askstring(
            "Extrair legenda",
            "Legenda para extrair: 1, 2, pt ou todas",
            initialvalue="1",
        )
        if not selector:
            return
        selector = selector.strip().lower()
        output_format = simpledialog.askstring(
            "Formato da legenda",
            "Formato: original ou srt",
            initialvalue="original",
        )
        if not output_format:
            return
        output_format = output_format.strip().lower()
        if output_format not in {"original", "srt"}:
            messagebox.showwarning("Formato da legenda", "Use: original ou srt.")
            return

        out_dir = self.output_dir("Legendas", "Extraidas_Opcoes_GUI")
        ensure_dir(out_dir)

        def chosen_tracks(video: Path) -> list[dict]:
            subtitles = [track for track in self.build_tracks(video) if track["type"] == "s"]
            if selector in {"todas", "todos", "all"}:
                return subtitles
            if selector in {"pt", "por"}:
                return [track for track in subtitles if track["language"] == "por"]
            if selector.isdigit():
                index = int(selector) - 1
                return subtitles[index:index + 1]
            return []

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for video_index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                tracks = chosen_tracks(video)
                if not tracks:
                    logs.append(f"[PULADO] {video.name} - legenda solicitada nao encontrada")
                    continue
                self.thread_status(f"Extraindo legenda ({video_index}/{len(videos)}): {video.name}")
                for number, track in enumerate(tracks, start=1):
                    language = track["language"] or "und"
                    if output_format == "srt":
                        extension = ".srt"
                        codec_args: list[str | Path] = ["-c:s", "srt"]
                    else:
                        extension = subtitle_extension(track["codec"])
                        codec_args = ["-c", "copy"]
                    suffix = selector if selector not in {"todas", "todos", "all"} else f"legenda{number}"
                    out_file = out_dir / f"{video.stem}_{suffix}_{language}{extension}"
                    self.thread_log(f"[LEGENDA {suffix.upper()}] {video.name}")
                    args = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video, "-map", f"0:{track['source_index']}", *codec_args, out_file]
                    result = self.run_command(args)
                    if result.returncode == 0:
                        ok += 1
                        logs.append(f"[OK] Legenda extraida: {out_file}")
                    elif result.returncode == -999:
                        return ok, logs
                    else:
                        logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Extrair legenda", f"Processo concluido. Legendas extraidas: {ok}")

        self.run_background("Extraindo legenda com opcoes... aguarde.", task, done)

    def mux_external_subtitle_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Juntar legenda", "Nenhum video encontrado.")
            return
        self.lift()
        self.focus_force()
        language = simpledialog.askstring("Idioma da legenda", "Codigo de idioma:", initialvalue="por", parent=self)
        if not language:
            return
        self.lift()
        self.focus_force()
        delay_text = simpledialog.askstring(
            "Atraso da legenda",
            "Atraso/adiantamento em ms (0 padrao, negativo adianta):",
            initialvalue="0",
            parent=self,
        )
        try:
            offset = f"{int(delay_text or '0') / 1000:.3f}"
        except ValueError:
            offset = "0.000"
        out_dir = self.output_dir("Legendas", "Mux_Externa_GUI")
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Juntando legenda ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[MUX LEGENDA] {video.name}")
                subtitles = find_subtitle_sidecars(video)
                if not subtitles:
                    logs.append(f"[PULADO] {video.name} - legenda externa nao encontrada")
                    continue
                out_file = out_dir / f"{video.stem}.mkv"
                tracks = self.build_tracks(video)
                video_extras = [track for track in tracks if track["type"] == "v" and track["relative"] > 0]
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                ]
                for subtitle in subtitles:
                    args.extend(["-itsoffset", offset, "-i", subtitle])
                args.extend([
                    "-map", "0:v:0?", "-map", "0:a?",
                ])
                for subtitle_index in range(len(subtitles)):
                    args.extend(["-map", f"{subtitle_index + 1}:0"])
                args.extend(["-map", "0:s?"])
                for extra in video_extras:
                    args.extend(["-map", f"0:{extra['source_index']}"])
                args.extend([
                    "-map", "0:t?", "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                    "-disposition:s", "0",
                ])
                full_default_set = False
                for subtitle_index, subtitle in enumerate(subtitles):
                    out_subtitle_index = subtitle_index
                    is_forced = subtitle_sidecar_is_forced(subtitle)
                    args.extend([f"-metadata:s:s:{out_subtitle_index}", f"language={subtitle_sidecar_language(subtitle, language)}"])
                    if is_forced:
                        args.extend([f"-disposition:s:{out_subtitle_index}", "forced"])
                    elif not full_default_set:
                        args.extend([f"-disposition:s:{out_subtitle_index}", "default"])
                        full_default_set = True
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Legenda(s) juntada(s): {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Juntar legenda", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Juntando legenda externa... aguarde.", task, done)

    def mux_external_audio_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Juntar audio", "Nenhum video encontrado.")
            return
        language = simpledialog.askstring("Idioma do audio", "Codigo de idioma:", initialvalue="por")
        if not language:
            return
        make_default = messagebox.askyesno("Audio default", "Tornar o audio adicionado default?")
        delay_text = simpledialog.askstring("Atraso do audio", "Atraso/adiantamento em ms (0 padrao, negativo adianta):", initialvalue="0")
        try:
            offset = f"{int(delay_text or '0') / 1000:.3f}"
        except ValueError:
            offset = "0.000"
        out_dir = self.output_dir("Audio", "Mux_Externo_GUI")
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Juntando audio ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[MUX AUDIO] {video.name}")
                audio = find_sidecar(video, AUDIO_EXTENSIONS)
                if not audio:
                    logs.append(f"[PULADO] {video.name} - audio externo nao encontrado")
                    continue
                out_file = out_dir / f"{video.stem}.mkv"
                audio_count = len([track for track in self.build_tracks(video) if track["type"] == "a"])
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    "-itsoffset", offset, "-i", audio,
                    "-map", "0", "-map", "1:a:0",
                    "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                    f"-metadata:s:a:{audio_count}", f"language={language.strip().lower()[:3]}",
                ]
                if make_default:
                    args.extend(["-disposition:a", "0", f"-disposition:a:{audio_count}", "default"])
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Audio juntado: {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Juntar audio", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Juntando audio externo... aguarde.", task, done)

    def cover_map_args(self, file_path: Path) -> list[str]:
        args = []
        for track in self.build_tracks(file_path):
            remove = False
            if track["type"] == "t" and ("image/" in track["title"].lower() or "cover" in track["title"].lower()):
                remove = True
            if track["type"] == "v" and track["relative"] > 0:
                remove = track["codec"].lower() in IMAGE_VIDEO_CODECS or "cover" in track["title"].lower() or "image/" in track["title"].lower()
            if not remove:
                args.extend(["-map", f"0:{track['source_index']}"])
        return args

    def remove_covers_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Remover capas", "Nenhum video encontrado.")
            return
        if not messagebox.askyesno("Remover capas", "Remover capas/anexos de imagem dos videos da pasta?"):
            return
        out_dir = self.output_dir("Capas", "Sem_Capa_GUI")
        ensure_dir(out_dir)
        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Removendo capas ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[REMOVER CAPA] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video, *self.cover_map_args(video), "-map_metadata", "0", "-map_chapters", "0", "-c", "copy", out_file]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Sem capa: {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Remover capas", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Removendo capas... aguarde.", task, done)

    def clean_metadata_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Metadados", "Nenhum video encontrado.")
            return
        if not messagebox.askyesno("Metadados", "Limpar metadados textuais dos videos da pasta?"):
            return
        out_dir = self.output_dir("Metadados", "Limpos_GUI")
        ensure_dir(out_dir)
        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Limpando metadados ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[METADADOS] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args: list[str | Path] = [self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video, "-map", "0", "-map_metadata", "0", "-map_chapters", "0", "-c", "copy"]
                for key in GLOBAL_METADATA_KEYS:
                    args.extend(["-metadata", f"{key}="])
                tracks = self.build_tracks(video)
                counters = {"v": 0, "a": 0, "s": 0}
                for track in tracks:
                    if track["type"] in counters:
                        relative = counters[track["type"]]
                        counters[track["type"]] += 1
                        args.extend([f"-metadata:s:{track['type']}:{relative}", "title="])
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Metadados limpos: {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Metadados", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Limpando metadados... aguarde.", task, done)

    def apply_local_cover_batch(self) -> None:
        cover = next((self.work_dir / name for name in COVER_NAMES if (self.work_dir / name).exists()), None)
        if not cover:
            messagebox.showwarning("Cover local", "Nao encontrei cover.jpg, cover.jpeg ou cover.png na pasta.")
            return
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Cover local", "Nenhum video encontrado.")
            return
        if not messagebox.askyesno("Cover local", f"Aplicar {cover.name} nos videos da pasta?"):
            return
        out_dir = self.output_dir("Capas_GUI")
        ensure_dir(out_dir)
        mimetype = "image/png" if cover.suffix.lower() == ".png" else "image/jpeg"
        filename = "cover.png" if cover.suffix.lower() == ".png" else "cover.jpg"
        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Aplicando cover local ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[CAPA LOCAL] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *self.cover_map_args(video), "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                    "-attach", cover, "-metadata:s:t", f"mimetype={mimetype}", "-metadata:s:t:0", f"filename={filename}", out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Capa aplicada: {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Cover local", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Aplicando cover local... aguarde.", task, done)

    def apply_cache_cover_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Cache de capas", "Nenhum video encontrado.")
            return
        query, season = _detect_cache_query(videos)
        if not query:
            query = self.tmdb_query_text()
        if not query:
            messagebox.showinfo("Cache de capas", "Nao consegui identificar um nome para buscar no cache.")
            return
        cover, expected_dir = _cached_cover_path(query, season)
        if not cover:
            message = f"Nenhuma capa encontrada no cache para:\n{query}"
            if season is not None:
                message += f"\nTemporada: {season}"
            if expected_dir:
                message += f"\n\nPasta esperada:\n{expected_dir}"
            messagebox.showwarning("Cache de capas", message)
            return
        if not messagebox.askyesno("Cache de capas", f"Aplicar capa do cache?\n\n{cover}"):
            return

        out_dir = self.output_dir("Capas_Cache_GUI")
        ensure_dir(out_dir)
        mimetype = "image/png" if cover.suffix.lower() == ".png" else "image/jpeg"
        filename = "cover.png" if cover.suffix.lower() == ".png" else "cover.jpg"

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"Aplicando capa do cache ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[CAPA CACHE] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *self.cover_map_args(video), "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                    "-attach", cover, "-metadata:s:t", f"mimetype={mimetype}", "-metadata:s:t:0", f"filename={filename}", out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Capa do cache aplicada: {out_file}")
                elif result.returncode == -999:
                    break
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Cache de capas", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Aplicando capa do cache... aguarde.", task, done)

    def choose_tmdb_result(self, results: list[dict]) -> dict | None:
        self.tmdb_results = results
        self.tmdb_list.delete(0, tk.END)
        self.cover_preview_image = None
        self.cover_preview_path = None
        if hasattr(self, "cover_preview_label"):
            self.cover_preview_label.configure(image="", text="Sem prévia")
        for item in results:
            kind = "Série" if item.get("media_type") == "tv" else "Filme"
            title = item.get("name") or item.get("title") or "Sem título"
            date = item.get("first_air_date") or item.get("release_date") or ""
            year = f" ({date[:4]})" if date else ""
            self.tmdb_list.insert(tk.END, f"{kind} - {title}{year}")
        if results:
            self.tmdb_list.selection_set(0)
            self.log_line("Resultados TMDb carregados. Selecione um item e clique em Aplicar selecionado.")
        else:
            self.log_line("[AVISO] Nenhum resultado TMDb encontrado.")
        self.update_apply_metadata_button_state()
        return None

    def clear_tmdb_search(self) -> None:
        self.tmdb_query_var.set("")
        self.tmdb_placeholder_active = False
        self.show_tmdb_placeholder()
        self.tmdb_results = []
        self.tmdb_list.delete(0, tk.END)
        self.cover_preview_image = None
        self.cover_preview_path = None
        if hasattr(self, "cover_preview_label"):
            self.cover_preview_label.configure(image="", text="Sem prévia")
        self.update_apply_metadata_button_state()
        self.status_var.set("Busca TMDb limpa.")

    def default_tmdb_query(self) -> str:
        query = self.tmdb_query_text()
        if query:
            return query
        videos = self.video_files_in_folder()
        if videos:
            detected_query, _season = _detect_cache_query(videos)
            if detected_query:
                return detected_query
        if self.current_file:
            return " ".join(self.current_file.stem.replace(".", " ").replace("_", " ").split())
        return ""

    def show_cover_preview_from_file(self, cover_path: Path) -> bool:
        preview_dir = self.config_data.app_root / "Capas"
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_png = preview_dir / "_tmdb_gui_preview.png"
        try:
            result = run_hidden([
                self.tools.ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                cover_path,
                "-vf",
                f"scale={COVER_PREVIEW_WIDTH}:{COVER_PREVIEW_HEIGHT}:force_original_aspect_ratio=decrease",
                preview_png,
            ])
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Falha ao converter imagem para prévia.")
            self.cover_preview_image = tk.PhotoImage(file=str(preview_png))
            self.cover_preview_path = cover_path
            if self.cover_preview_frame is not None:
                self.cover_preview_frame.configure(
                    width=self.cover_preview_image.width() + COVER_PREVIEW_FRAME_PAD_X,
                    height=self.cover_preview_image.height() + COVER_PREVIEW_FRAME_PAD_Y,
                )
            self.cover_preview_label.configure(image=self.cover_preview_image, text="")
            return True
        except Exception as exc:
            self.log_line(f"[AVISO] Falha ao carregar prévia: {exc}")
            return False

    def auto_tmdb_lookup_for_folder(self) -> None:
        if not self.auto_tmdb_on_folder_var.get():
            return
        if not self.video_files:
            return
        folder_key = str(self.work_dir.resolve())
        if self.last_auto_tmdb_dir == folder_key:
            return
        self.last_auto_tmdb_dir = folder_key
        query, season = _detect_cache_query(self.video_files)
        if not query:
            query = self.default_tmdb_query()
        if not query:
            return
        self.tmdb_query_var.set(query)
        self.tmdb_placeholder_active = False

        cover, _expected_dir = _cached_cover_path(query, season)
        if cover:
            self.tmdb_results = []
            self.tmdb_list.delete(0, tk.END)
            self.update_apply_metadata_button_state()
            self.show_cover_preview_from_file(cover)
            self.status_var.set(f"Capa encontrada no cache para: {query}")
            self.log_line(f"[CACHE] Prévia carregada automaticamente: {cover}")
            return

        if not self.has_tmdb_key():
            self.log_line(f"[INFO] Busca automática: cache não encontrado para {query}. TMDb sem chave configurada.")
            return
        try:
            results = search_multi(query.strip(), self.work_dir)
        except Exception as exc:
            self.log_line(f"[AVISO] Busca automática TMDb falhou: {exc}")
            return
        self.tmdb_result_mode = "cover"
        self.choose_tmdb_result(results)
        if results:
            self.status_var.set(f"Busca automática TMDb carregada para: {query}")
            self.preview_selected_tmdb_cover()

    def search_tmdb_cover_panel(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("TMDb", "Nenhum video encontrado.")
            return
        query = self.default_tmdb_query()
        if not query:
            messagebox.showinfo("TMDb", "Digite um nome no painel Metadados e capas.")
            return
        self.tmdb_query_var.set(query)
        try:
            results = search_multi(query.strip(), self.work_dir)
        except Exception as exc:
            messagebox.showerror("TMDb", f"Falha ao buscar no TMDb:\n{exc}")
            return
        self.tmdb_result_mode = "cover"
        self.choose_tmdb_result(results)
        if results:
            self.status_var.set(f"Resultados de capa carregados para: {query}")

    def search_tmdb_metadata_panel(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("TMDb", "Nenhum video encontrado.")
            return
        query = self.default_tmdb_query()
        if not query:
            messagebox.showinfo("TMDb", "Digite o nome do filme no painel Metadados e capas.")
            return
        self.tmdb_query_var.set(query)
        try:
            results = search_movies(query.strip(), self.work_dir)
        except Exception as exc:
            messagebox.showerror("TMDb", f"Falha ao buscar no TMDb:\n{exc}")
            return
        self.tmdb_result_mode = "metadata"
        self.choose_tmdb_result(results)
        if results:
            self.status_var.set(f"Resultados de metadados carregados para: {query}")

    def apply_tmdb_cover_batch(self) -> None:
        self.search_tmdb_cover_panel()

    def selected_tmdb_result(self) -> dict | None:
        selection = self.tmdb_list.curselection()
        if not selection or not self.tmdb_results:
            return None
        return self.tmdb_results[selection[0]]

    def tmdb_cover_info(self, chosen: dict, videos: list[Path]) -> tuple[str | None, str, str]:
        poster_path = chosen.get("poster_path")
        cache_folder = chosen.get("name") or chosen.get("title") or self.tmdb_query_text() or "TMDb"
        cache_name = "Serie"
        _query, season = _detect_cache_query(videos)
        if chosen.get("media_type") == "tv" and season is not None:
            try:
                details = season_details(int(chosen["id"]), season, self.work_dir)
                if details.get("poster_path"):
                    poster_path = details["poster_path"]
                    cache_name = f"Temporada {season}"
            except Exception as exc:
                self.log_line(f"[AVISO] Falha ao buscar capa da temporada: {exc}")
        elif chosen.get("media_type") == "movie":
            title = chosen.get("title") or cache_folder
            year = (chosen.get("release_date") or "")[:4]
            cache_folder = title
            cache_name = f"{title} ({year})" if year else title
        return poster_path, str(cache_folder), str(cache_name)

    def preview_selected_tmdb_cover(self) -> None:
        chosen = self.selected_tmdb_result()
        if not chosen:
            messagebox.showinfo("TMDb", "Busque e selecione um resultado TMDb primeiro.")
            return
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("TMDb", "Nenhum video encontrado.")
            return
        poster_path, _cache_folder, _cache_name = self.tmdb_cover_info(chosen, videos)
        if not poster_path:
            messagebox.showwarning("TMDb", "Resultado selecionado não possui capa.")
            return

        preview_dir = self.config_data.app_root / "Capas"
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_jpg = preview_dir / "_tmdb_gui_preview.jpg"
        preview_png = preview_dir / "_tmdb_gui_preview.png"
        try:
            download_poster(str(poster_path), preview_jpg)
            result = run_hidden([
                self.tools.ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                preview_jpg,
                "-vf",
                f"scale={COVER_PREVIEW_WIDTH}:{COVER_PREVIEW_HEIGHT}:force_original_aspect_ratio=decrease",
                preview_png,
            ])
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Falha ao converter imagem para prévia.")
            self.cover_preview_image = tk.PhotoImage(file=str(preview_png))
            self.cover_preview_path = preview_jpg
            if self.cover_preview_frame is not None:
                self.cover_preview_frame.configure(
                    width=self.cover_preview_image.width() + COVER_PREVIEW_FRAME_PAD_X,
                    height=self.cover_preview_image.height() + COVER_PREVIEW_FRAME_PAD_Y,
                )
            self.cover_preview_label.configure(image=self.cover_preview_image, text="")
            self.status_var.set("Prévia da capa carregada.")
        except Exception as exc:
            self.cover_preview_image = None
            self.cover_preview_path = None
            self.cover_preview_label.configure(image="", text="Falha na prévia")
            messagebox.showerror("TMDb", f"Não foi possível mostrar a prévia da capa:\n{exc}")

    def open_cover_preview(self) -> None:
        if not self.cover_preview_path or not self.cover_preview_path.exists():
            messagebox.showinfo("Prévia da capa", "Gere a prévia da capa primeiro.")
            return
        try:
            os.startfile(self.cover_preview_path)
        except OSError as exc:
            messagebox.showerror("Prévia da capa", f"Não foi possível abrir a imagem:\n{exc}")

    def apply_selected_tmdb_cover(self) -> None:
        chosen = self.selected_tmdb_result()
        if not chosen:
            messagebox.showinfo("TMDb", "Busque e selecione um resultado TMDb primeiro.")
            return
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("TMDb", "Nenhum video encontrado.")
            return

        out_dir = self.output_dir("Capas_TMDB_GUI")
        ensure_dir(out_dir)
        temp_cover = self.config_data.app_root / "Capas" / "_tmdb_gui_cover.jpg"
        poster_path, cache_folder, cache_name = self.tmdb_cover_info(chosen, videos)
        if not poster_path:
            messagebox.showwarning("TMDb", "Resultado selecionado não possui capa.")
            return

        def task() -> tuple[int, list[str]]:
            logs = []
            ok = 0
            self.thread_status("Baixando capa TMDb...")
            download_poster(str(poster_path), temp_cover)
            cache_path = self.config_data.local_covers_dir / _safe_name(str(cache_folder)) / f"{_safe_name(str(cache_name))}.jpg"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(temp_cover.read_bytes())
            logs.append(f"[OK] Capa salva no cache: {cache_path}")
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Aplicando capa TMDb ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[TMDB] Aplicando capa em: {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                args = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *self.cover_map_args(video), "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                    "-attach", temp_cover, "-metadata:s:t", "mimetype=image/jpeg", "-metadata:s:t:0", "filename=cover.jpg", out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Capa TMDb aplicada: {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("TMDb", f"Processo concluído. Arquivos OK: {ok}")

        self.run_background("Baixando e aplicando capa TMDb... aguarde.", task, done)

    def apply_selected_tmdb_metadata(self) -> None:
        selection = self.tmdb_list.curselection()
        if not selection or not self.tmdb_results:
            messagebox.showinfo("TMDb", "Busque e selecione um filme TMDb primeiro.")
            return
        chosen = self.tmdb_results[selection[0]]
        if chosen.get("media_type") == "tv":
            messagebox.showinfo("TMDb", "Metadados pela GUI estao preparados para filmes. Para series, use apenas a capa por enquanto.")
            return
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("TMDb", "Nenhum video encontrado.")
            return
        title = chosen.get("title") or chosen.get("name") or self.tmdb_query_text() or "Filme"
        year = (chosen.get("release_date") or chosen.get("first_air_date") or "")[:4]
        overview = chosen.get("overview") or ""
        if not messagebox.askyesno("TMDb", f"Inserir metadados de:\n{title} {year}\n\nArquivos: {len(videos)}"):
            return

        out_dir = self.output_dir("Metadados", "TMDb_GUI")
        ensure_dir(out_dir)
        temp_cover = self.config_data.app_root / "Capas" / "_tmdb_gui_metadata_cover.jpg"
        poster_path = chosen.get("poster_path")

        def task() -> tuple[int, list[str]]:
            logs = []
            ok = 0
            if poster_path:
                self.thread_status("Baixando capa TMDb para metadados...")
                download_poster(str(poster_path), temp_cover)
            out_base = _safe_name(f"{title} {year}".strip()) or "Filme TMDb"
            for index, video in enumerate(videos, start=1):
                self.thread_status(f"Inserindo metadados TMDb ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[TMDB METADADOS] {video.name}")
                out_file = out_dir / f"{out_base}.mkv"
                if len(videos) > 1:
                    out_file = out_dir / f"{out_base} - {video.stem}.mkv"
                suffix = 2
                while out_file.exists():
                    out_file = out_dir / f"{out_file.stem} ({suffix}).mkv"
                    suffix += 1

                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *self.cover_map_args(video), "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                ]
                for key in GLOBAL_METADATA_KEYS:
                    args.extend(["-metadata", f"{key}="])
                tracks = self.build_tracks(video)
                counters = {"v": 0, "a": 0, "s": 0}
                for track in tracks:
                    if track["type"] in counters:
                        relative = counters[track["type"]]
                        counters[track["type"]] += 1
                        args.extend([f"-metadata:s:{track['type']}:{relative}", "title="])
                args.extend([
                    "-metadata", f"title={title}",
                    "-metadata", f"description={overview}",
                    "-metadata", f"synopsis={overview}",
                    "-metadata", f"date={year}",
                ])
                if poster_path and temp_cover.exists():
                    args.extend([
                        "-attach", temp_cover,
                        "-metadata:s:t", "mimetype=image/jpeg",
                        "-metadata:s:t:0", "filename=cover.jpg",
                    ])
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Metadados TMDb inseridos: {out_file}")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("TMDb", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Inserindo metadados TMDb... aguarde.", task, done)

    def ask_smart_movie_options(self) -> dict[str, bool] | None:
        dialog = tk.Toplevel(self)
        dialog.title("Modo Inteligente Filme")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        result: dict[str, bool] | None = None
        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Escolha as etapas desta execução.", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))

        variables: dict[str, tk.BooleanVar] = {
            "external_subtitle": tk.BooleanVar(value=True),
            "filter_tracks": tk.BooleanVar(value=True),
            "clean_metadata": tk.BooleanVar(value=True),
            "insert_metadata": tk.BooleanVar(value=True),
            "apply_cover": tk.BooleanVar(value=True),
            "save_cover_cache": tk.BooleanVar(value=True),
        }
        labels = [
            ("external_subtitle", "Juntar legenda externa se existir"),
            ("filter_tracks", "Manter áudio PT + EN e legenda PT"),
            ("clean_metadata", "Limpar metadados antigos"),
            ("insert_metadata", "Inserir metadados TMDb"),
            ("apply_cover", "Aplicar capa TMDb"),
            ("save_cover_cache", "Salvar capa no cache"),
        ]
        for key, label in labels:
            ttk.Checkbutton(frame, text=label, variable=variables[key]).pack(anchor=tk.W, pady=2)

        buttons = ttk.Frame(frame)
        buttons.pack(anchor=tk.E, pady=(12, 0))

        def start() -> None:
            nonlocal result
            result = {key: variable.get() for key, variable in variables.items()}
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        ttk.Button(buttons, text="Iniciar rotina", command=start).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="Cancelar", command=cancel).pack(side=tk.LEFT)
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = self.winfo_rootx() + max(0, (self.winfo_width() - width) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - height) // 2)
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
        return result

    def smart_movie_mode_gui(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Modo Inteligente", "Nenhum video encontrado.")
            return
        if len(videos) != 1:
            messagebox.showwarning("Modo Inteligente", "Esta rotina foi feita para um filme por pasta. Deixe somente um video na pasta.")
            return
        selection = self.tmdb_list.curselection()
        if not selection or not self.tmdb_results:
            query = self.default_tmdb_query()
            if query:
                self.tmdb_query_var.set(query)
                self.search_tmdb_metadata_panel()
            messagebox.showinfo(
                "Modo Inteligente",
                "Passo 1: busque o filme no painel 'Metadados e capas'.\n"
                "Passo 2: selecione o filme correto na lista 'Metadados e capas'.\n"
                "Passo 3: clique em '2 Executar'.",
            )
            return
        movie = self.tmdb_results[selection[0]]
        if movie.get("media_type") == "tv":
            messagebox.showinfo("Modo Inteligente", "Modo Inteligente da GUI esta preparado para filmes.")
            return
        options = self.ask_smart_movie_options()
        if not options:
            return

        source = videos[0]
        out_dir = self.output_dir("Modo_Inteligente_GUI")
        ensure_dir(out_dir)
        temp_dir = self.temp_work_dir("_temp_modo_inteligente_gui")
        ensure_dir(temp_dir)

        def map_pt_en_pt_subtitle_tracks(file_path: Path) -> tuple[list[dict], list[str] | None]:
            tracks = self.build_tracks(file_path)
            videos_keep = [track for track in tracks if track["type"] == "v"]
            audios_pt = [track for track in tracks if track["type"] == "a" and track["language"] == "por"]
            audios_en = [track for track in tracks if track["type"] == "a" and track["language"] in {"eng", "en"}]
            subs_pt = sorted(
                [track for track in tracks if track["type"] == "s" and track["language"] == "por"],
                key=lambda track: (0 if track["forced"] else 1, track["relative"]),
            )
            attachments = [track for track in tracks if track["type"] in {"t", "d"}]
            missing = []
            if not audios_pt:
                missing.append("audio PT")
            if not audios_en:
                missing.append("audio EN")
            if not subs_pt:
                missing.append("legenda PT")
            if missing:
                return [], missing
            return [*videos_keep, *audios_pt, *audios_en, *subs_pt, *attachments], None

        if options["filter_tracks"]:
            _kept_tracks, missing_tracks = map_pt_en_pt_subtitle_tracks(source)
            if options["external_subtitle"] and find_subtitle_sidecars(source):
                missing_tracks = [item for item in missing_tracks if item != "legenda PT"]
            if missing_tracks:
                missing_text = ", ".join(missing_tracks)
                if not messagebox.askyesno(
                    "Modo Inteligente Filme",
                    "A etapa 'Manter áudio PT + EN e legenda PT' não encontrou todas as faixas esperadas.\n\n"
                    f"Arquivo: {source.name}\n"
                    f"Faltando: {missing_text}\n\n"
                    "Deseja continuar ignorando essa etapa e executar as demais funções?",
                ):
                    return
                options["filter_tracks"] = False

        def task() -> tuple[int, list[str]]:
            logs = []
            current = source
            subtitles = find_subtitle_sidecars(source) if options["external_subtitle"] else []
            if subtitles:
                self.thread_status(f"Modo Inteligente: juntando legenda externa em {source.name}")
                temp_sub = temp_dir / "01_legenda_externa.mkv"
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", source,
                ]
                for subtitle in subtitles:
                    args.extend(["-i", subtitle])
                args.extend(["-map", "0:v:0?", "-map", "0:a?"])
                for subtitle_index in range(len(subtitles)):
                    args.extend(["-map", f"{subtitle_index + 1}:0"])
                args.extend(["-map", "0:s?", "-map", "0:t?"])
                args.extend(["-map_metadata", "0", "-map_chapters", "0", "-c", "copy", "-disposition:s", "0"])
                full_default_set = False
                for subtitle_index, subtitle in enumerate(subtitles):
                    out_subtitle_index = subtitle_index
                    is_forced = subtitle_sidecar_is_forced(subtitle)
                    args.extend([f"-metadata:s:s:{out_subtitle_index}", f"language={subtitle_sidecar_language(subtitle, 'por')}"])
                    if is_forced:
                        args.extend([f"-disposition:s:{out_subtitle_index}", "forced"])
                    elif not full_default_set:
                        args.extend([f"-disposition:s:{out_subtitle_index}", "default"])
                        full_default_set = True
                args.append(temp_sub)
                result = self.run_command(args)
                if result.returncode != 0:
                    logs.append(f"[ERRO] Falha ao juntar legenda externa: {result.stderr.strip()}")
                    return 0, logs
                current = temp_sub
                logs.append(f"[OK] Legenda(s) externa(s) juntada(s): {', '.join(subtitle.name for subtitle in subtitles)}")
            elif options["external_subtitle"]:
                logs.append("[INFO] Nenhuma legenda externa encontrada. Seguindo...")
            else:
                logs.append("[INFO] Etapa de legenda externa ignorada nesta execução.")

            if options["filter_tracks"]:
                self.thread_status(f"Modo Inteligente: filtrando PT+EN/Legenda PT em {source.name}")
                temp_filtered = temp_dir / "02_filtrado.mkv"
                kept_tracks, missing = map_pt_en_pt_subtitle_tracks(current)
                if missing:
                    logs.append(f"[PULADO] Faltando na rotina final: {', '.join(missing)}")
                    return 0, logs
                map_args = []
                for track in kept_tracks:
                    map_args.extend(["-map", f"0:{track['source_index']}"])
                args = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", current,
                    *map_args, "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                    "-disposition:a", "0", "-disposition:s", "0",
                    "-disposition:a:0", "default",
                ]
                subtitle_index = 0
                full_default_set = False
                for track in kept_tracks:
                    if track["type"] != "s":
                        continue
                    flags = []
                    if not track["forced"] and not full_default_set:
                        flags.append("default")
                        full_default_set = True
                    if track["forced"]:
                        flags.append("forced")
                    if track["hearing_impaired"]:
                        flags.append("hearing_impaired")
                    if flags:
                        args.extend([f"-disposition:s:{subtitle_index}", "+".join(flags)])
                    subtitle_index += 1
                args.append(temp_filtered)
                result = self.run_command(args)
                if result.returncode != 0:
                    logs.append(f"[ERRO] Falha ao filtrar PT+EN/Legenda PT: {result.stderr.strip()}")
                    return 0, logs
                current = temp_filtered
            else:
                logs.append("[INFO] Etapa PT+EN/Legenda PT ignorada nesta execução.")

            title = movie.get("title") or source.stem
            year = (movie.get("release_date") or "")[:4]
            overview = movie.get("overview") or ""
            out_file = out_dir / f"{_safe_name(f'{title} {year}'.strip())}.mkv"
            poster_path = movie.get("poster_path")
            temp_cover = temp_dir / "cover.jpg"
            if options["apply_cover"] and poster_path:
                self.thread_status("Modo Inteligente: baixando capa TMDb...")
                download_poster(str(poster_path), temp_cover)
                if options["save_cover_cache"]:
                    cache_name = f"{title} ({year})" if year else title
                    cache_path = self.config_data.local_covers_dir / _safe_name(title) / f"{_safe_name(cache_name)}.jpg"
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_bytes(temp_cover.read_bytes())
                    logs.append(f"[OK] Capa salva no cache: {cache_path}")
            elif not options["apply_cover"]:
                logs.append("[INFO] Etapa de capa TMDb ignorada nesta execução.")

            self.thread_status(f"Modo Inteligente: gerando arquivo final {out_file.name}")
            cover_map_args = self.cover_map_args(current) if temp_cover.exists() else ["-map", "0"]
            args = [
                self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", current,
                *cover_map_args, "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
            ]
            if options["clean_metadata"]:
                for key in GLOBAL_METADATA_KEYS:
                    args.extend(["-metadata", f"{key}="])
                for selector in ("v", "a", "s"):
                    count = len([track for track in self.build_tracks(current) if track["type"] == selector])
                    for index in range(count):
                        args.extend([f"-metadata:s:{selector}:{index}", "title="])
            if options["insert_metadata"]:
                args.extend([
                    "-metadata", f"title={title}",
                    "-metadata", f"description={overview}",
                    "-metadata", f"synopsis={overview}",
                    "-metadata", f"date={year}",
                ])
            if temp_cover.exists():
                args.extend(["-attach", temp_cover, "-metadata:s:t", "mimetype=image/jpeg", "-metadata:s:t:0", "filename=cover.jpg"])
            args.append(out_file)
            result = self.run_command(args)
            if result.returncode == 0:
                logs.append(f"[OK] Modo Inteligente gerou: {out_file}")
                return 1, logs
            logs.append(f"[ERRO] Falha ao gerar arquivo final: {result.stderr.strip()}")
            return 0, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Modo Inteligente", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Modo Inteligente em andamento... aguarde.", task, done)

    def ask_smart_series_options(self) -> dict | None:
        dialog = tk.Toplevel(self)
        dialog.title("Modo Inteligente Série")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        result: dict | None = None

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Configure a rotina antes de iniciar.",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))

        codec_var = tk.StringVar(value="H.265 / HEVC")
        container_var = tk.StringVar(value="MKV")
        audio_var = tk.StringVar(value="AAC 256 kbps")
        quality_var = tk.StringVar(value="Equilibrado (CQ/CRF 26)")
        resolution_var = tk.StringVar(value="Original")
        filter_var = tk.StringVar(value="None")
        step_vars: dict[str, tk.BooleanVar] = {
            "external_subtitle": tk.BooleanVar(value=True),
            "recode_video": tk.BooleanVar(value=True),
            "keep_pt_en_audio": tk.BooleanVar(value=True),
            "keep_pt_subtitles": tk.BooleanVar(value=True),
            "clean_metadata": tk.BooleanVar(value=True),
            "apply_cover": tk.BooleanVar(value=True),
            "save_cover_cache": tk.BooleanVar(value=True),
        }
        subtitle_language_var = tk.StringVar(value="por")
        subtitle_delay_var = tk.StringVar(value="0")

        rows = [
            ("Codec:", codec_var, ("H.265 / HEVC", "H.264", "AV1")),
            ("Container:", container_var, ("MKV", "MP4")),
            ("Áudio:", audio_var, ("AAC 256 kbps", "AAC 320 kbps", "AC3 640 kbps", "copy")),
            ("Qualidade:", quality_var, ("Alta (CQ/CRF 23)", "Equilibrado (CQ/CRF 26)", "Compacto (CQ/CRF 28)")),
            ("Resolução:", resolution_var, RESOLUTION_OPTIONS),
            ("Filtro:", filter_var, ("None", "Deinterlace", "Denoise leve", "Denoise medio", "Denoise forte", "Remaster leve", "Remaster medio", "Remaster forte")),
        ]

        combos: list[ttk.Combobox] = []
        video_option_combos: list[ttk.Combobox] = []
        for index, (label, variable, values) in enumerate(rows, start=1):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky=tk.W, padx=(0, 10), pady=4)
            combo = ttk.Combobox(frame, textvariable=variable, values=values, state="readonly", width=30)
            combo.grid(row=index, column=1, sticky=tk.EW, pady=4)
            combos.append(combo)
            if label in {"Codec:", "Qualidade:", "Resolução:", "Filtro:"}:
                video_option_combos.append(combo)

        steps_frame = ttk.LabelFrame(frame, text="Etapas desta execução")
        steps_frame.grid(row=len(rows) + 1, column=0, columnspan=2, sticky=tk.EW, pady=(12, 4))
        step_labels = [
            ("external_subtitle", "Juntar legenda externa se existir"),
            ("recode_video", "Converter vídeo"),
            ("keep_pt_en_audio", "Manter apenas áudio PT + EN"),
            ("keep_pt_subtitles", "Manter apenas legendas PT"),
            ("clean_metadata", "Limpar metadados antigos"),
            ("apply_cover", "Aplicar capa TMDb"),
            ("save_cover_cache", "Salvar capa no cache"),
        ]
        subtitle_options = ttk.Frame(steps_frame)
        subtitle_options.grid(row=4, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=(4, 2))
        ttk.Label(subtitle_options, text="Idioma legenda:").pack(side=tk.LEFT, padx=(0, 6))
        subtitle_language_entry = ttk.Entry(subtitle_options, textvariable=subtitle_language_var, width=6)
        subtitle_language_entry.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(subtitle_options, text="Atraso ms:").pack(side=tk.LEFT, padx=(0, 6))
        subtitle_delay_entry = ttk.Entry(subtitle_options, textvariable=subtitle_delay_var, width=8)
        subtitle_delay_entry.pack(side=tk.LEFT)

        def update_recode_options() -> None:
            state = "readonly" if step_vars["recode_video"].get() else tk.DISABLED
            for combo in video_option_combos:
                combo.configure(state=state)

        def update_subtitle_options() -> None:
            state = tk.NORMAL if step_vars["external_subtitle"].get() else tk.DISABLED
            subtitle_language_entry.configure(state=state)
            subtitle_delay_entry.configure(state=state)

        for index, (key, label) in enumerate(step_labels):
            command = None
            if key == "recode_video":
                command = update_recode_options
            elif key == "external_subtitle":
                command = update_subtitle_options
            ttk.Checkbutton(steps_frame, text=label, variable=step_vars[key], command=command).grid(
                row=index // 2,
                column=index % 2,
                sticky=tk.W,
                padx=8,
                pady=2,
            )
        update_recode_options()
        update_subtitle_options()

        note = ttk.Label(
            frame,
            text="Padrão recomendado: MKV, H.265, AAC 256 kbps, qualidade equilibrada.",
        )
        note.grid(row=len(rows) + 2, column=0, columnspan=2, sticky=tk.W, pady=(10, 4))

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(rows) + 3, column=0, columnspan=2, sticky=tk.E, pady=(12, 0))

        def start() -> None:
            nonlocal result
            result = {
                "codec": codec_var.get(),
                "container": container_var.get(),
                "audio": audio_var.get(),
                "quality": quality_var.get(),
                "resolution": resolution_var.get(),
                "filter": filter_var.get(),
                "subtitle_language": subtitle_language_var.get().strip().lower()[:3] or "por",
                "subtitle_delay_ms": subtitle_delay_var.get().strip() or "0",
                **{key: variable.get() for key, variable in step_vars.items()},
            }
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        ttk.Button(buttons, text="Iniciar rotina", command=start).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="Cancelar", command=cancel).pack(side=tk.LEFT)

        dialog.protocol("WM_DELETE_WINDOW", cancel)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = self.winfo_rootx() + max(0, (self.winfo_width() - width) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - height) // 2)
        dialog.geometry(f"+{x}+{y}")
        if combos:
            combos[0].focus_set()
        self.wait_window(dialog)
        return result

    def smart_series_mode_gui(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Modo Inteligente Série", "Nenhum video encontrado.")
            return
        selection = self.tmdb_list.curselection()
        if not selection or not self.tmdb_results:
            query = self.default_tmdb_query()
            if query:
                self.tmdb_query_var.set(query)
                self.search_tmdb_cover_panel()
            messagebox.showinfo(
                "Modo Inteligente Série",
                "Passo 1: clique em 'Buscar Série'.\n"
                "Passo 2: selecione a série correta em 'Metadados e capas'.\n"
                "Passo 3: clique em 'Modo Inteligente Série'.",
            )
            return
        chosen = self.tmdb_results[selection[0]]
        if chosen.get("media_type") != "tv":
            messagebox.showinfo("Modo Inteligente Série", "Selecione um resultado de Série no TMDb.")
            return

        options = self.ask_smart_series_options()
        if not options:
            return
        codec = self.codec_from_text(options["codec"])
        container = "mp4" if options["container"].lower() == "mp4" else "mkv"
        extension = ".mp4" if container == "mp4" else ".mkv"
        resolution = options["resolution"]
        if options.get("recode_video", True):
            resolution = self.resolve_resolution_choice(resolution, "Modo Inteligente Série")
            if resolution is None:
                return
        filter_chain = self.filter_chain_from_options(resolution, options["filter"])
        audio_mode = options["audio"]
        quality = options["quality"]
        if not options.get("recode_video", True):
            filter_chain = ""
        try:
            subtitle_offset = f"{int(str(options.get('subtitle_delay_ms', '0')) or '0') / 1000:.3f}"
        except ValueError:
            subtitle_offset = "0.000"
        subtitle_language = str(options.get("subtitle_language", "por")).strip().lower()[:3] or "por"
        if False and not messagebox.askyesno(
            "Modo Inteligente Série",
            "Executar rotina inteligente para série?\n\n"
            "Saída: MKV H.265/HEVC\n"
            f"Qualidade: {quality}\n"
            f"Áudio: {audio_mode}\n"
            "Faixas mantidas: áudio PT + EN e legendas PT.\n"
            "Capa: TMDb da série/temporada detectada.",
        ):
            return

        out_dir = self.output_dir("Modo_Inteligente_Serie_GUI")
        ensure_dir(out_dir)
        temp_dir = self.temp_work_dir("_temp_modo_inteligente_serie_gui")
        ensure_dir(temp_dir)
        poster_path, cache_folder, cache_name = self.tmdb_cover_info(chosen, videos)
        if options.get("apply_cover", True) and not poster_path:
            messagebox.showwarning("Modo Inteligente Série", "Resultado selecionado não possui capa.")
            return
        temp_cover = temp_dir / "cover.jpg"

        def series_kept_tracks(video: Path) -> tuple[list[dict], list[str]]:
            tracks = self.build_tracks(video)
            video_tracks = [
                track for track in tracks
                if track["type"] == "v"
                and track["relative"] == 0
                and track["codec"].lower() not in IMAGE_VIDEO_CODECS
            ]
            audio_tracks = [track for track in tracks if track["type"] == "a"]
            subtitle_tracks = [track for track in tracks if track["type"] == "s"]
            audio_pt = [track for track in audio_tracks if track["language"] == "por"]
            audio_en = [track for track in audio_tracks if track["language"] in {"eng", "en"}]
            subs_pt = sorted(
                [track for track in subtitle_tracks if track["language"] == "por"],
                key=lambda track: (0 if track["forced"] else 1, track["relative"]),
            )
            kept_audio = [*audio_pt, *audio_en] if options.get("keep_pt_en_audio", True) else audio_tracks
            kept_subtitles = subs_pt if options.get("keep_pt_subtitles", True) else subtitle_tracks
            missing = []
            if not video_tracks:
                missing.append("vídeo principal")
            if options.get("keep_pt_en_audio", True) and not audio_pt:
                missing.append("áudio PT")
            if options.get("keep_pt_en_audio", True) and not audio_en:
                missing.append("áudio EN")
            if options.get("keep_pt_subtitles", True) and not subs_pt:
                missing.append("legenda PT")
            return [*video_tracks[:1], *kept_audio, *kept_subtitles], missing

        if options.get("keep_pt_en_audio", True) or options.get("keep_pt_subtitles", True):
            missing_by_file = []
            truncated_missing = False
            for video in videos:
                _kept_tracks, missing_tracks = series_kept_tracks(video)
                if options.get("external_subtitle", True) and find_subtitle_sidecars(video):
                    missing_tracks = [item for item in missing_tracks if item != "legenda PT"]
                relevant_missing = [
                    item for item in missing_tracks
                    if item in {"áudio PT", "áudio EN", "legenda PT"}
                ]
                if relevant_missing:
                    missing_by_file.append(f"{video.name}: {', '.join(relevant_missing)}")
                if len(missing_by_file) >= 8:
                    truncated_missing = True
                    break
            if missing_by_file:
                more_text = ""
                if truncated_missing:
                    more_text = "\n\nA lista foi resumida para não ocupar a tela inteira."
                if not messagebox.askyesno(
                    "Modo Inteligente Série",
                    "A etapa 'Manter áudio PT + EN e legenda PT' não encontrou todas as faixas esperadas.\n\n"
                    + "\n".join(missing_by_file)
                    + more_text
                    + "\n\nDeseja continuar ignorando essa etapa e executar as demais funções?",
                ):
                    return
                options["keep_pt_en_audio"] = False
                options["keep_pt_subtitles"] = False

        def mux_external_subtitle_for_series(video: Path, index: int) -> tuple[Path, str | None]:
            subtitles = find_subtitle_sidecars(video)
            if not subtitles:
                return video, f"[INFO] {video.name} - legenda externa não encontrada"
            temp_sub = temp_dir / f"{index:03d}_legenda_externa.mkv"
            tracks = self.build_tracks(video)
            video_extras = [track for track in tracks if track["type"] == "v" and track["relative"] > 0]
            args: list[str | Path] = [
                self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
            ]
            for subtitle in subtitles:
                args.extend(["-itsoffset", subtitle_offset, "-i", subtitle])
            args.extend(["-map", "0:v:0?", "-map", "0:a?"])
            for subtitle_index in range(len(subtitles)):
                args.extend(["-map", f"{subtitle_index + 1}:0"])
            args.extend(["-map", "0:s?"])
            for extra in video_extras:
                args.extend(["-map", f"0:{extra['source_index']}"])
            args.extend([
                "-map", "0:t?", "-map_metadata", "0", "-map_chapters", "0", "-c", "copy",
                "-disposition:s", "0",
            ])
            full_default_set = False
            for subtitle_index, subtitle in enumerate(subtitles):
                out_subtitle_index = subtitle_index
                is_forced = subtitle_sidecar_is_forced(subtitle)
                args.extend([f"-metadata:s:s:{out_subtitle_index}", f"language={subtitle_sidecar_language(subtitle, subtitle_language)}"])
                if is_forced:
                    args.extend([f"-disposition:s:{out_subtitle_index}", "forced"])
                elif not full_default_set:
                    args.extend([f"-disposition:s:{out_subtitle_index}", "default"])
                    full_default_set = True
            args.append(temp_sub)
            result = self.run_command(args)
            if result.returncode == 0:
                return temp_sub, f"[OK] Legenda(s) externa(s) juntada(s): {', '.join(subtitle.name for subtitle in subtitles)}"
            if result.returncode == -999:
                return video, None
            return video, f"[ERRO] Falha ao juntar legenda em {video.name}: {result.stderr.strip()}"

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            if options.get("apply_cover", True) and poster_path:
                self.thread_status("Modo Inteligente Série: baixando capa TMDb...")
                download_poster(str(poster_path), temp_cover)
                if options.get("save_cover_cache", True):
                    cache_path = self.config_data.local_covers_dir / _safe_name(str(cache_folder)) / f"{_safe_name(str(cache_name))}.jpg"
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_bytes(temp_cover.read_bytes())
                    logs.append(f"[OK] Capa salva no cache: {cache_path}")
            else:
                logs.append("[INFO] Etapa de capa TMDb ignorada nesta execução.")

            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                current_video = video
                if options.get("external_subtitle", True):
                    self.thread_status(f"Modo Inteligente Série: juntando legenda externa ({index}/{len(videos)}): {video.name}")
                    self.thread_log(f"[MODO SÉRIE] Legenda externa: {video.name}")
                    current_video, mux_log = mux_external_subtitle_for_series(video, index)
                    if mux_log:
                        logs.append(mux_log)
                    if mux_log and mux_log.startswith("[ERRO]"):
                        continue
                    if self.cancel_event.is_set():
                        break
                else:
                    logs.append(f"[INFO] {video.name} - etapa de legenda externa ignorada")

                kept, missing = series_kept_tracks(current_video)
                if not kept or not any(track["type"] == "v" for track in kept):
                    logs.append(f"[PULADO] {video.name} - sem vídeo principal compatível")
                    continue
                if not any(track["type"] == "a" for track in kept):
                    logs.append(f"[PULADO] {video.name} - sem áudio PT/EN")
                    continue
                if missing:
                    logs.append(f"[AVISO] {video.name} - faltando: {', '.join(missing)}")

                self.thread_status(f"Modo Inteligente Série ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[MODO SÉRIE] {video.name}")
                out_file = out_dir / f"{video.stem}{extension}"
                args: list[str | Path] = [
                    self.tools.ffmpeg,
                    "-y",
                    "-loglevel",
                    "error",
                    "-nostats",
                    "-i",
                    current_video,
                ]
                mapped_tracks = []
                for track in kept:
                    if container == "mp4" and track["type"] == "s" and track["codec"].lower() not in {"subrip", "ass", "ssa", "webvtt", "mov_text"}:
                        logs.append(f"[AVISO] {video.name} - legenda {track['codec']} ignorada para MP4")
                        continue
                    mapped_tracks.append(track)
                    args.extend(["-map", f"0:{track['source_index']}"])
                if filter_chain:
                    args.extend(["-vf", filter_chain])
                args.extend([
                    "-map_metadata", "0",
                    "-map_chapters", "0",
                    *(self.video_encoder_args(codec, quality) if options.get("recode_video", True) else ["-c:v", "copy"]),
                    *self.audio_output_args(audio_mode),
                    *self.subtitle_output_args(container),
                    "-disposition:a", "0",
                ])
                if any(track["type"] == "s" for track in mapped_tracks):
                    args.extend(["-disposition:s", "0"])
                if options.get("clean_metadata", True):
                    for key in GLOBAL_METADATA_KEYS:
                        args.extend(["-metadata", f"{key}="])

                audio_index = 0
                subtitle_index = 0
                full_default_set = False
                if options.get("clean_metadata", True):
                    args.extend(["-metadata:s:v:0", "title="])
                for track in mapped_tracks:
                    if track["type"] == "a":
                        args.extend([f"-metadata:s:a:{audio_index}", f"language={track['language']}"])
                        if options.get("clean_metadata", True):
                            args.extend([f"-metadata:s:a:{audio_index}", "title="])
                        if audio_index == 0:
                            args.extend([f"-disposition:a:{audio_index}", "default"])
                        audio_index += 1
                    elif track["type"] == "s":
                        args.extend([f"-metadata:s:s:{subtitle_index}", f"language={track['language']}"])
                        if options.get("clean_metadata", True):
                            args.extend([f"-metadata:s:s:{subtitle_index}", "title="])
                        flags = []
                        if not track["forced"] and not full_default_set:
                            flags.append("default")
                            full_default_set = True
                        if track["forced"]:
                            flags.append("forced")
                        if track["hearing_impaired"]:
                            flags.append("hearing_impaired")
                        if flags:
                            args.extend([f"-disposition:s:{subtitle_index}", "+".join(flags)])
                        subtitle_index += 1

                if options.get("apply_cover", True) and temp_cover.exists() and container == "mkv":
                    args.extend([
                        "-attach", temp_cover,
                        "-metadata:s:t", "mimetype=image/jpeg",
                        "-metadata:s:t:0", "filename=cover.jpg",
                    ])
                elif options.get("apply_cover", True) and container == "mp4":
                    logs.append(f"[AVISO] {video.name} - capa embutida ignorada no MP4")
                args.append(out_file)
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Modo Inteligente Série: {out_file}")
                elif result.returncode == -999:
                    break
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Modo Inteligente Série", f"Processo concluído. Arquivos OK: {ok}")

        self.run_background("Modo Inteligente Série em andamento... aguarde.", task, done)

    def codec_from_text(self, value: str) -> str:
        if value.startswith("Vídeo copy") or value.startswith("Video copy"):
            return "copy"
        if value.startswith("H.264"):
            return "h264"
        if value.startswith("AV1"):
            return "av1"
        return "hevc"

    def quality_from_text(self, value: str) -> str:
        if "23" in value:
            return "23"
        if "26" in value:
            return "26"
        return "28"

    def resolve_resolution_choice(self, resolution: str, title: str) -> str | None:
        if resolution != "Personalizada":
            return resolution
        height = simpledialog.askinteger(
            title,
            "Informe a altura da resolução personalizada em pixels.\n"
            "Exemplo: 960, 1200, 1600.\n\n"
            "A largura será calculada automaticamente mantendo o aspecto.",
            minvalue=120,
            maxvalue=4320,
            parent=self,
        )
        if height is None:
            return None
        if height % 2:
            height += 1
        return f"{height}p"

    def append_filter_preset(self, filters: list[str], selected_filter: str) -> None:
        if selected_filter == "Deinterlace":
            filters.append("yadif=0:-1:0")
        elif selected_filter == "Denoise leve":
            filters.append("hqdn3d=1.5:1.5:6:6")
        elif selected_filter == "Denoise medio":
            filters.append("hqdn3d=2.5:2.5:8:8")
        elif selected_filter == "Denoise forte":
            filters.append("hqdn3d=4:4:10:10")
        elif selected_filter == "Denoise":
            filters.append("hqdn3d=1.5:1.5:6:6")
        elif selected_filter == "Granulado leve":
            filters.append("noise=alls=4:allf=t+u")
        elif selected_filter == "Granulado medio":
            filters.append("noise=alls=8:allf=t+u")
        elif selected_filter == "Granulado forte":
            filters.append("noise=alls=12:allf=t+u")
        elif selected_filter == "Remaster leve":
            filters.append("hqdn3d=0.8:0.8:3:3")
            filters.append("unsharp=3:3:0.30:3:3:0.15")
        elif selected_filter == "Remaster medio":
            filters.append("hqdn3d=1.2:1.2:4:4")
            filters.append("unsharp=5:5:0.55:3:3:0.25")
        elif selected_filter == "Remaster forte":
            filters.append("hqdn3d=2:2:6:6")
            filters.append("unsharp=5:5:0.75:3:3:0.35")
        elif selected_filter == "Remaster":
            filters.append("hqdn3d=0.8:0.8:3:3")
            filters.append("unsharp=3:3:0.30:3:3:0.15")

    def compose_filter_chain_from_presets(self, resolution: str, selected_filters: list[str]) -> str:
        filters: list[str] = []
        for selected_filter in selected_filters:
            normalized = self.normalize_filter_value(selected_filter)
            if normalized in {"", "Nenhum", "None"}:
                continue
            self.append_filter_preset(filters, normalized)

        if resolution not in {"Original", "Manter"}:
            match = re.fullmatch(r"(\d+)p", resolution)
            if match:
                filters.append(f"scale=-2:{match.group(1)}:flags=lanczos")
                filters.append("setsar=1")
        if any(self.normalize_filter_value(value).startswith("Remaster") for value in selected_filters):
            filters.append("format=yuv420p")

        return ",".join(filters)

    def filter_chain_from_options(self, resolution: str, selected_filter: str) -> str:
        return self.compose_filter_chain_from_presets(resolution, [selected_filter])

    def selected_conversion_filter_chain(self, resolution: str) -> str:
        selected_filters: list[str] = []
        if self.conversion_deinterlace_var.get():
            selected_filters.append("Deinterlace")
        selected_filter = self.filter_value()
        if selected_filter != "Nenhum":
            selected_filters.append(selected_filter)
        return self.compose_filter_chain_from_presets(resolution, selected_filters)

    def detect_black_crop(self, file_path: Path) -> tuple[str | None, str]:
        """Detecta crop seguro para bordas pretas usando alguns segundos do video."""
        try:
            result = run_hidden([
                self.tools.ffmpeg,
                "-hide_banner",
                "-ss",
                "00:00:20",
                "-t",
                "12",
                "-i",
                file_path,
                "-vf",
                "cropdetect=24:16:0",
                "-an",
                "-f",
                "null",
                "-",
            ])
        except Exception as exc:
            return None, f"[BORDAS] {file_path.name}: falha ao detectar bordas: {exc}"
        output = f"{result.stdout}\n{result.stderr}"
        crops = re.findall(r"crop=(\d+:\d+:\d+:\d+)", output)
        if not crops:
            return None, f"[BORDAS] {file_path.name}: nenhuma borda preta relevante detectada."
        crop = crops[-1]
        try:
            width, height, x_offset, y_offset = (int(part) for part in crop.split(":"))
            original = self.build_tracks(file_path)
            video = next((track for track in original if track["type"] == "v" and track["relative"] == 0), None)
            streams = ffprobe_streams(self.tools, file_path)
            video_stream = next((stream for stream in streams if str(stream.get("codec_type", "")).lower() == "video"), None)
            src_width = int(video_stream.get("width", 0)) if video_stream else 0
            src_height = int(video_stream.get("height", 0)) if video_stream else 0
        except Exception:
            return None, f"[BORDAS] {file_path.name}: crop detectado, mas nao foi possivel validar: {crop}"
        if not src_width or not src_height:
            return None, f"[BORDAS] {file_path.name}: crop detectado, mas dimensoes originais nao foram lidas: {crop}"
        crop_w = src_width - width
        crop_h = src_height - height
        if crop_w < 8 and crop_h < 8:
            return None, f"[BORDAS] {file_path.name}: nenhuma borda relevante detectada."
        if width < src_width * 0.70 or height < src_height * 0.70:
            return None, f"[BORDAS] {file_path.name}: crop descartado por ser agressivo demais: {crop}"
        if x_offset % 2 or y_offset % 2 or width % 2 or height % 2:
            return None, f"[BORDAS] {file_path.name}: crop descartado por dimensoes impares: {crop}"
        _ = video  # mantem a validacao acima explicita para leitura futura.
        return f"crop={crop}", f"[BORDAS] {file_path.name}: bordas detectadas e crop aplicado: crop={crop}"

    def compose_video_filter(self, base_filter: str, file_path: Path, remove_borders: bool, logs: list[str]) -> str:
        filters: list[str] = []
        if remove_borders:
            crop_filter, message = self.detect_black_crop(file_path)
            self.thread_log(message)
            if crop_filter:
                filters.append(crop_filter)
        if base_filter:
            filters.append(base_filter)
        return ",".join(filters)

    def subtitle_output_args(self, container: str) -> list[str]:
        if container == "mp4":
            return ["-c:s", "mov_text"]
        return ["-c:s", "copy"]

    def selected_codec(self) -> str:
        return self.codec_from_text(self.codec_var.get())

    def selected_quality(self) -> str:
        return self.quality_from_text(self.quality_var.get())

    def video_encoder_args(self, codec: str, quality_text: str | None = None) -> list[str]:
        cq = self.quality_from_text(quality_text) if quality_text is not None else self.selected_quality()
        return video_encoder_args(self.tools, codec, cq)

    def selected_container(self) -> str:
        return "mp4" if self.container_var.get().lower() == "mp4" else "mkv"

    def compatible_map_args(self, file_path: Path, container: str) -> tuple[list[str], list[str], list[str]]:
        if container != "mp4":
            return ["-map", "0:v:0?", "-map", "0:a?", "-map", "0:s?", "-map", "0:t?"], ["-c:s", "copy"], []

        warnings = []
        map_args = []
        text_subtitles = {"subrip", "ass", "ssa", "webvtt", "mov_text"}
        for track in self.build_tracks(file_path):
            codec = track["codec"].lower()
            if track["type"] == "t":
                warnings.append(f"[AVISO] Anexo ignorado para MP4 em: {file_path.name}")
                continue
            if track["type"] == "v" and track["relative"] > 0:
                warnings.append(f"[AVISO] Faixa de imagem/video extra ignorada para MP4 em: {file_path.name}")
                continue
            if track["type"] == "s" and codec not in text_subtitles:
                warnings.append(f"[AVISO] Legenda {codec} ignorada para MP4 em: {file_path.name}")
                continue
            map_args.extend(["-map", f"0:{track['source_index']}"])
        return map_args, ["-c:s", "mov_text"], warnings

    def audio_output_args(self, audio_mode: str | None = None) -> list[str]:
        selected_audio = audio_mode if audio_mode is not None else self.audio_mode_var.get()
        audio_text = selected_audio.lower()
        if audio_text.startswith("aac 320"):
            return ["-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
        if audio_text.startswith("aac"):
            return ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
        if audio_text.startswith("ac3"):
            return ["-c:a", "ac3", "-b:a", "640k", "-ar", "48000"]
        return ["-c:a", "copy"]

    def selected_filter_chain(self) -> str:
        return self.filter_chain_from_options(self.resolution_var.get(), self.filter_value())

    def source_video_codec(self, file_path: Path) -> str | None:
        for track in self.build_tracks(file_path):
            if track["type"] != "v" or track["relative"] != 0:
                continue
            codec = track["codec"].lower()
            if codec in {"h264", "avc1"}:
                return "h264"
            if codec in {"hevc", "h265"}:
                return "hevc"
            if codec == "av1":
                return "av1"
            return None
        return None

    def source_video_dimensions(self, file_path: Path) -> tuple[int, int]:
        streams = ffprobe_streams(self.tools, file_path)
        video_stream = next((stream for stream in streams if str(stream.get("codec_type", "")).lower() == "video"), None)
        if not video_stream:
            return 0, 0
        try:
            return int(video_stream.get("width", 0)), int(video_stream.get("height", 0))
        except (TypeError, ValueError):
            return 0, 0

    def media_duration_seconds(self, file_path: Path) -> float:
        result = run_hidden([
            self.tools.ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            file_path,
        ])
        if result.returncode != 0:
            return 0.0
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0

    def aspect_scale_filter(self, file_path: Path, target_aspect: str) -> tuple[str | None, str]:
        src_width, src_height = self.source_video_dimensions(file_path)
        if not src_width or not src_height:
            return None, f"[ASPECTO] {file_path.name}: nao foi possivel ler a resolucao original."
        ratios = {
            "4:3": (4, 3),
            "16:9": (16, 9),
            "21:9": (21, 9),
        }
        ratio_w, ratio_h = ratios.get(target_aspect, (4, 3))
        target_width = int(round(src_height * ratio_w / ratio_h))
        if target_width % 2:
            target_width += 1
        target_height = src_height if src_height % 2 == 0 else src_height - 1
        if target_width < 2 or target_height < 2:
            return None, f"[ASPECTO] {file_path.name}: resolucao calculada invalida para {target_aspect}."
        return (
            f"scale={target_width}:{target_height}:flags=lanczos,setsar=1",
            f"[ASPECTO] {file_path.name}: recode para {target_aspect} em {target_width}x{target_height}.",
        )

    def fix_aspect_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Corrigir Aspecto", "Nenhum video encontrado.")
            return
        target_aspect = self.aspect_target_var.get()
        container = "mp4" if self.aspect_container_var.get().lower() == "mp4" else "mkv"
        extension = ".mp4" if container == "mp4" else ".mkv"
        audio_mode = self.aspect_audio_var.get()
        quality = self.aspect_quality_var.get()
        copy_mode = bool(self.aspect_copy_first_var.get())
        mode_text = "sem recode" if copy_mode else "com recode"
        summary = (
            "Corrigir aspecto em lote?\n\n"
            f"Aspecto de saida: {target_aspect}\n"
            f"Modo: {mode_text}\n"
            f"Container: {container.upper()}\n"
            f"Audio: {'copy' if copy_mode else audio_mode}\n"
            f"Qualidade: {'sem perda' if copy_mode else quality}\n\n"
            "No modo sem recode, apenas a proporcao informada ao player sera alterada."
        )
        if not messagebox.askyesno("Corrigir Aspecto", summary):
            return
        out_dir = self.output_dir("Aspecto_GUI", target_aspect.replace(":", "x"))
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"Corrigir aspecto ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[ASPECTO] {video.name}")
                out_file = out_dir / f"{video.stem}{extension}"
                map_args, subtitle_args, warnings = self.compatible_map_args(video, container)
                for warning in warnings:
                    self.thread_log(warning)
                if copy_mode:
                    args: list[str | Path] = [
                        self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                        *map_args,
                        "-c", "copy",
                        "-aspect", target_aspect,
                        "-map_metadata", "0",
                        "-map_chapters", "0",
                        out_file,
                    ]
                    self.thread_log(f"[ASPECTO] {video.name}: ajustando para {target_aspect} sem recode.")
                else:
                    codec = self.source_video_codec(video) or "hevc"
                    video_filter, message = self.aspect_scale_filter(video, target_aspect)
                    self.thread_log(message)
                    if not video_filter:
                        logs.append(f"[ERRO] {video.name}: nao foi possivel calcular correcao de aspecto.")
                        continue
                    args = [
                        self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                        *map_args,
                        "-vf", video_filter,
                        *self.video_encoder_args(codec, quality),
                        *self.audio_output_args(audio_mode),
                        *subtitle_args,
                        "-map_metadata", "0",
                        "-map_chapters", "0",
                        out_file,
                    ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Aspecto corrigido: {out_file}")
                elif result.returncode == -999:
                    break
                elif result.returncode == -998:
                    logs.append(f"[PULADO] {out_file.name} - arquivo ja existe")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Corrigir Aspecto", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Corrigindo aspecto em lote... aguarde.", task, done)

    def detect_black_crop_aggressive(self, file_path: Path) -> tuple[str | None, str]:
        src_width, src_height = self.source_video_dimensions(file_path)
        duration = self.media_duration_seconds(file_path)
        if duration > 90:
            points = [0.10, 0.25, 0.40, 0.55, 0.70, 0.85]
            offsets = [max(20, min(duration - 20, duration * point)) for point in points]
        else:
            offsets = [20]

        crop_limits = [18, 24, 32, 48, 64, 80, 96]
        candidates: list[tuple[str, int, int, int, int]] = []
        details = []
        for offset in offsets:
            offset_found = False
            offset_full_frame = False
            for limit in crop_limits:
                try:
                    result = run_hidden([
                        self.tools.ffmpeg,
                        "-hide_banner",
                        "-ss",
                        f"{offset:.2f}",
                        "-t",
                        "8",
                        "-i",
                        file_path,
                        "-vf",
                        f"cropdetect={limit}:16:0",
                        "-an",
                        "-f",
                        "null",
                        "-",
                    ])
                except Exception as exc:
                    details.append(f"{offset:.0f}s limit {limit} falhou: {exc}")
                    continue

                output = f"{result.stdout}\n{result.stderr}"
                crops = re.findall(r"crop=(\d+:\d+:\d+:\d+)", output)
                if not crops:
                    continue
                crop = crops[-1]
                try:
                    width, height, x_offset, y_offset = (int(part) for part in crop.split(":"))
                except ValueError:
                    details.append(f"{offset:.0f}s limit {limit} crop invalido {crop}")
                    continue
                if src_width and src_height and width == src_width and height == src_height and x_offset == 0 and y_offset == 0:
                    offset_full_frame = True
                    continue
                if width < 64 or height < 64:
                    details.append(f"{offset:.0f}s limit {limit} pequeno demais {crop}")
                    continue
                if src_width and src_height and (width < src_width * 0.40 or height < src_height * 0.40):
                    details.append(f"{offset:.0f}s limit {limit} extremo demais {crop}")
                    continue
                if x_offset % 2 or y_offset % 2 or width % 2 or height % 2:
                    details.append(f"{offset:.0f}s limit {limit} dimensoes impares {crop}")
                    continue
                candidates.append((crop, width, height, x_offset, y_offset))
                details.append(f"{offset:.0f}s limit {limit} {crop}")
                offset_found = True
                break
            if not offset_found and offset_full_frame:
                details.append(f"{offset:.0f}s quadro inteiro em todos os limits")
            elif not offset_found:
                details.append(f"{offset:.0f}s sem crop util")

        if not candidates:
            detail_text = "; ".join(details[:8]) if details else "sem detalhes"
            return None, f"[BORDAS] {file_path.name}: nenhuma borda util detectada automaticamente. Amostras: {detail_text}"

        counts: dict[str, int] = {}
        for crop, *_ in candidates:
            counts[crop] = counts.get(crop, 0) + 1

        def candidate_score(item: tuple[str, int, int, int, int]) -> tuple[int, int]:
            crop, width, height, _x, _y = item
            removed = (src_width - width if src_width else 0) + (src_height - height if src_height else 0)
            return counts.get(crop, 0), removed

        crop, width, height, x_offset, y_offset = max(candidates, key=candidate_score)

        if width < 64 or height < 64:
            return None, f"[BORDAS] {file_path.name}: crop descartado por gerar video pequeno demais: {crop}"
        if src_width and src_height and width == src_width and height == src_height and x_offset == 0 and y_offset == 0:
            return None, f"[BORDAS] {file_path.name}: crop escolhido retornou o quadro inteiro ({crop}); nenhuma borda util foi detectada automaticamente."
        if src_width and src_height and (width < src_width * 0.40 or height < src_height * 0.40):
            return None, f"[BORDAS] {file_path.name}: crop descartado por ser extremo demais: {crop}"
        if x_offset % 2 or y_offset % 2 or width % 2 or height % 2:
            return None, f"[BORDAS] {file_path.name}: crop descartado por dimensoes impares: {crop}"

        if src_width and src_height:
            detail_text = "; ".join(details[:8])
            return (
                f"crop={crop}",
                f"[BORDAS] {file_path.name}: entrada {src_width}x{src_height}; crop escolhido: crop={crop}; saida apos corte {width}x{height}. Amostras: {detail_text}",
            )
        return f"crop={crop}", f"[BORDAS] {file_path.name}: crop agressivo aplicado: crop={crop}."

    def manual_border_values(self) -> tuple[int, int, int, int] | None:
        try:
            left = int(self.borders_left_var.get().strip() or "0")
            right = int(self.borders_right_var.get().strip() or "0")
            top = int(self.borders_top_var.get().strip() or "0")
            bottom = int(self.borders_bottom_var.get().strip() or "0")
        except ValueError:
            return None
        return left, right, top, bottom

    def has_manual_border_values(self) -> bool:
        values = self.manual_border_values()
        return bool(values and any(value != 0 for value in values))

    def manual_crop_filter(self, file_path: Path) -> tuple[str | None, str]:
        values = self.manual_border_values()
        if values is None:
            return None, "[BORDAS] Corte manual invalido: use apenas numeros inteiros."
        left, right, top, bottom = values

        if min(left, right, top, bottom) < 0:
            return None, "[BORDAS] Corte manual invalido: os valores nao podem ser negativos."
        if left == right == top == bottom == 0:
            return None, "[BORDAS] Corte manual vazio: informe ao menos um valor para cortar."
        if any(value % 2 for value in (left, right, top, bottom)):
            return None, "[BORDAS] Corte manual invalido: use valores pares para maior compatibilidade."

        src_width, src_height = self.source_video_dimensions(file_path)
        if not src_width or not src_height:
            return None, f"[BORDAS] {file_path.name}: nao foi possivel ler a resolucao original."

        width = src_width - left - right
        height = src_height - top - bottom
        if width < 64 or height < 64:
            return None, f"[BORDAS] {file_path.name}: corte manual geraria video pequeno demais: {width}x{height}."
        if width % 2 or height % 2:
            return None, f"[BORDAS] {file_path.name}: corte manual geraria dimensoes impares: {width}x{height}."

        crop = f"{width}:{height}:{left}:{top}"
        return (
            f"crop={crop}",
            f"[BORDAS] {file_path.name}: entrada {src_width}x{src_height}; corte manual aplicado: crop={crop}; saida apos corte {width}x{height}.",
        )

    def border_resolution_filter(self, resolution: str | None = None) -> str:
        resolution = resolution or self.borders_resolution_var.get()
        if resolution not in {"Original", "Manter"}:
            match = re.fullmatch(r"(\d+)p", resolution)
            if match:
                return f"scale=-2:{match.group(1)}:flags=lanczos"
        return ""

    def border_crop_filter_for_file(self, file_path: Path) -> tuple[str | None, str]:
        mode = self.borders_mode_var.get().lower()
        if self.has_manual_border_values():
            return self.manual_crop_filter(file_path)
        if "manual" in mode:
            return self.manual_crop_filter(file_path)
        return self.detect_black_crop_aggressive(file_path)

    def border_video_filter_for_file(self, file_path: Path, resolution: str | None = None) -> tuple[str | None, list[str]]:
        logs = []
        crop_filter, message = self.border_crop_filter_for_file(file_path)
        logs.append(message)
        if not crop_filter:
            return None, logs
        filters = [crop_filter]
        scale_filter = self.border_resolution_filter(resolution)
        if scale_filter:
            filters.append(scale_filter)
        filters.append("setsar=1")
        return ",".join(filters), logs

    def analyze_borders_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Corrigir Bordas", "Nenhum video encontrado.")
            return
        resolution = self.resolve_resolution_choice(self.borders_resolution_var.get(), "Corrigir Bordas")
        if resolution is None:
            return
        self.log_line("=========================================================")
        self.log_line("  ANALISE DE BORDAS - MULTIPONTO")
        self.log_line("=========================================================")
        for video in videos:
            crop_filter, logs = self.border_video_filter_for_file(video, resolution)
            for line in logs:
                self.log_line(line)
            if crop_filter:
                self.log_line(f"[BORDAS] {video.name}: filtro final previsto: {crop_filter}")

    def fix_borders_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Corrigir Bordas", "Nenhum video encontrado.")
            return
        codec = self.codec_from_text(self.borders_codec_var.get())
        container = "mp4" if self.borders_container_var.get().lower() == "mp4" else "mkv"
        extension = ".mp4" if container == "mp4" else ".mkv"
        audio_mode = self.borders_audio_var.get()
        quality = self.borders_quality_var.get()
        resolution = self.resolve_resolution_choice(self.borders_resolution_var.get(), "Corrigir Bordas")
        if resolution is None:
            return
        summary = (
            "Corrigir bordas em lote?\n\n"
            f"Modo: {self.borders_mode_var.get()}\n"
            f"Codec: {self.borders_codec_var.get()}\n"
            f"Container: {container.upper()}\n"
            f"Audio: {audio_mode}\n"
            f"Qualidade: {quality}\n"
            f"Resolucao: {resolution}\n\n"
            "Esta rotina sempre faz encode porque corta pixels do video."
        )
        if not messagebox.askyesno("Corrigir Bordas", summary):
            return

        out_dir = self.output_dir("Bordas_GUI")
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"Corrigir bordas ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[BORDAS] {video.name}")
                video_filter, filter_logs = self.border_video_filter_for_file(video, resolution)
                for line in filter_logs:
                    self.thread_log(line)
                if not video_filter:
                    logs.extend(filter_logs)
                    continue
                out_file = out_dir / f"{video.stem}{extension}"
                map_args, subtitle_args, warnings = self.compatible_map_args(video, container)
                for warning in warnings:
                    self.thread_log(warning)
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *map_args,
                    "-vf", video_filter,
                    *self.video_encoder_args(codec, quality),
                    *self.audio_output_args(audio_mode),
                    *subtitle_args,
                    "-map_metadata", "0",
                    "-map_chapters", "0",
                    out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Bordas corrigidas: {out_file}")
                elif result.returncode == -999:
                    break
                elif result.returncode == -998:
                    logs.append(f"[PULADO] {out_file.name} - arquivo ja existe")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Corrigir Bordas", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Corrigindo bordas em lote... aguarde.", task, done)

    def filter_only_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Filtros", "Nenhum video encontrado.")
            return
        selected_filter = self.normalize_filter_value(self.filter_only_type_var.get())
        audio_mode = self.filter_only_audio_var.get()
        quality = self.filter_only_quality_var.get()
        remove_borders = bool(self.filter_only_crop_var.get())
        summary = (
            "Aplicar filtro em lote preservando o codec/container quando compativel?\n\n"
            f"Filtro: {selected_filter}\n"
            f"Audio: {audio_mode}\n"
            f"Qualidade: {quality}\n\n"
            f"Remover bordas pretas: {'sim' if remove_borders else 'nao'}\n\n"
            "Arquivos com codec/container nao compativel serao pulados e avisados no log."
        )
        if not messagebox.askyesno("Filtros", summary):
            return
        filter_chain = self.filter_chain_from_options("Original", selected_filter)
        out_dir = self.output_dir("Filtros_GUI", _safe_name(selected_filter))
        ensure_dir(out_dir)

        def task() -> tuple[int, list[str]]:
            ok = 0
            skipped = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"Filtro ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[FILTRO] {selected_filter}: {video.name}")
                extension = video.suffix.lower()
                if extension not in {".mkv", ".mp4"}:
                    skipped += 1
                    logs.append(f"[AVISO] {video.name}: container nao suportado para preservar formato. Converta primeiro para MKV ou MP4.")
                    continue
                codec = self.source_video_codec(video)
                if codec is None:
                    skipped += 1
                    logs.append(f"[AVISO] {video.name}: codec de video nao suportado para filtro direto. Converta primeiro para H.264, H.265 ou AV1.")
                    continue
                container = "mp4" if extension == ".mp4" else "mkv"
                out_file = out_dir / f"{video.stem}{extension}"
                map_args, subtitle_args, warnings = self.compatible_map_args(video, container)
                for warning in warnings:
                    self.thread_log(warning)
                video_filter = self.compose_video_filter(filter_chain, video, remove_borders, logs)
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *map_args,
                    "-vf", video_filter,
                    *self.video_encoder_args(codec, quality),
                    *self.audio_output_args(audio_mode),
                    *subtitle_args,
                    "-map_metadata", "0",
                    "-map_chapters", "0",
                    out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Filtro aplicado: {out_file}")
                elif result.returncode == -999:
                    break
                elif result.returncode == -998:
                    skipped += 1
                    logs.append(f"[PULADO] {out_file.name} - arquivo ja existe")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            if skipped:
                logs.append(f"[INFO] Arquivos pulados: {skipped}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Filtros", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Aplicando filtro em lote... aguarde.", task, done)

    def remaster_batch(self) -> None:
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Remasterizar", "Nenhum video encontrado.")
            return
        level = self.remaster_level_var.get() if hasattr(self, "remaster_level_var") else "Remaster leve"
        resolution = self.remaster_upscale_var.get() if hasattr(self, "remaster_upscale_var") else "Original"
        resolution = self.resolve_resolution_choice(resolution, "Remasterizar")
        if resolution is None:
            return
        audio_mode = self.remaster_audio_var.get() if hasattr(self, "remaster_audio_var") else "copy"
        remove_borders = bool(self.remaster_crop_var.get())
        deinterlace = bool(self.remaster_deinterlace_var.get())
        normalize_volume = bool(self.remaster_normalize_var.get())
        effective_audio_mode = "AAC 256 kbps" if normalize_volume and audio_mode == "copy" else audio_mode
        summary = (
            "Iniciar remaster em lote com estas opções?\n\n"
            f"Vídeo: H.265 / HEVC CQ/CRF 23\n"
            f"Container: MKV\n"
            f"Áudio: {effective_audio_mode}\n"
            f"Resolução: {resolution}\n"
            f"Filtro: {level}\n"
            f"Deinterlace: {'sim' if deinterlace else 'nao'}\n"
            f"Normalizar volume: {'sim' if normalize_volume else 'nao'}\n"
            f"Remover bordas pretas: {'sim' if remove_borders else 'nao'}"
        )
        if not messagebox.askyesno("Remasterizar", summary):
            return
        out_dir = self.output_dir("Remaster_GUI")
        ensure_dir(out_dir)
        filter_presets = ["Deinterlace", level] if deinterlace else [level]
        filter_chain = self.compose_filter_chain_from_presets(resolution, filter_presets)
        audio_filter_args: list[str] = []
        if normalize_volume:
            audio_filter_args = ["-af", "loudnorm=I=-16:LRA=11:TP=-1.5"]
        audio_args = self.audio_output_args(effective_audio_mode)

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"Remasterizar ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[REMASTER] {video.name}")
                out_file = out_dir / f"{video.stem}.mkv"
                video_filter = self.compose_video_filter(filter_chain, video, remove_borders, logs)
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    "-map", "0:v:0?", "-map", "0:a?", "-map", "0:s?", "-map", "0:t?",
                    "-vf", video_filter,
                    *self.video_encoder_args("hevc", "23"),
                    *audio_filter_args,
                    *audio_args,
                    "-c:s", "copy",
                    "-map_metadata", "0",
                    "-map_chapters", "0",
                    out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] Remaster: {out_file}")
                elif result.returncode == -999:
                    break
                elif result.returncode == -998:
                    logs.append(f"[PULADO] {out_file.name} - arquivo já existe")
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo("Remasterizar", f"Processo concluido. Arquivos OK: {ok}")

        self.run_background("Remasterizar em andamento... aguarde.", task, done)

    def convert_batch(self, action_name: str = "Processar", filter_override: str | None = None, output_folder: str = "Processados_GUI") -> None:
        codec = self.selected_codec()
        container = self.selected_container()
        extension = ".mp4" if container == "mp4" else ".mkv"
        videos = self.video_files_in_folder()
        if not videos:
            messagebox.showinfo("Converter", "Nenhum video encontrado.")
            return
        video_copy = codec == "copy"
        resolution = "Original"
        if not video_copy:
            resolution = self.resolve_resolution_choice(self.resolution_var.get(), action_name)
            if resolution is None:
                return
        elif (
            self.resolution_var.get() != "Original"
            or self.conversion_deinterlace_var.get()
            or self.filter_value() != "Nenhum"
            or self.conversion_crop_var.get()
        ):
            messagebox.showinfo(
                action_name,
                "Codec 'Vídeo copy' selecionado.\n\n"
                "Resolução, filtros e remoção de bordas serão ignorados, pois essas opções exigem recodificar o vídeo.",
            )
        if not messagebox.askyesno(action_name, f"Iniciar {action_name.lower()} em lote?"):
            return
        out_dir = self.output_dir(output_folder)
        ensure_dir(out_dir)
        if video_copy:
            filter_chain = ""
        elif filter_override:
            filter_chain = self.filter_chain_from_options(resolution, filter_override)
        else:
            filter_chain = self.selected_conversion_filter_chain(resolution)
        remove_borders = False if video_copy else bool(self.conversion_crop_var.get())

        def task() -> tuple[int, list[str]]:
            ok = 0
            logs = []
            for index, video in enumerate(videos, start=1):
                if self.cancel_event.is_set():
                    break
                self.thread_status(f"{action_name} ({index}/{len(videos)}): {video.name}")
                self.thread_log(f"[{action_name.upper()}] {video.name}")
                out_file = out_dir / f"{video.stem}{extension}"
                video_args = self.video_encoder_args(codec)
                filter_args: list[str] = []
                video_filter = self.compose_video_filter(filter_chain, video, remove_borders, logs) if remove_borders else filter_chain
                if video_filter:
                    filter_args = ["-vf", video_filter]
                map_args, subtitle_args, warnings = self.compatible_map_args(video, container)
                for warning in warnings:
                    self.thread_log(warning)
                args: list[str | Path] = [
                    self.tools.ffmpeg, "-y", "-loglevel", "error", "-nostats", "-i", video,
                    *map_args,
                    *filter_args,
                    *video_args,
                    *self.audio_output_args(),
                    *subtitle_args,
                    "-map_metadata", "0",
                    "-map_chapters", "0",
                    out_file,
                ]
                result = self.run_command(args)
                if result.returncode == 0:
                    ok += 1
                    logs.append(f"[OK] {action_name}: {out_file}")
                elif result.returncode == -999:
                    break
                else:
                    logs.append(f"[ERRO] {video.name}: {result.stderr.strip()}")
            return ok, logs

        def done(result: tuple[int, list[str]]) -> None:
            ok, logs = result
            for line in logs:
                self.log_line(line)
            self.set_last_output_dir(out_dir)
            messagebox.showinfo(action_name, f"Processo concluido. Arquivos OK: {ok}")

        self.run_background(f"{action_name} em andamento... aguarde.", task, done)


def main() -> None:
    initial_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
    app = TrackEditorApp(initial_dir)
    app.mainloop()


if __name__ == "__main__":
    main()
