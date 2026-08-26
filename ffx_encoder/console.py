from __future__ import annotations

import builtins
import ctypes
import re


STD_OUTPUT_HANDLE = -11
FOREGROUND_BLUE = 0x0001
FOREGROUND_GREEN = 0x0002
FOREGROUND_RED = 0x0004
FOREGROUND_INTENSITY = 0x0008

DEFAULT = FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE
COLORS = {
    "cyan": FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY,
    "green": FOREGROUND_GREEN | FOREGROUND_INTENSITY,
    "yellow": FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_INTENSITY,
    "red": FOREGROUND_RED | FOREGROUND_INTENSITY,
    "white": DEFAULT | FOREGROUND_INTENSITY,
}

_original_print = builtins.print
_kernel32 = ctypes.windll.kernel32
_stdout = _kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
_enabled = False


def set_color(color: str) -> None:
    _kernel32.SetConsoleTextAttribute(_stdout, COLORS.get(color, DEFAULT))


def reset_color() -> None:
    _kernel32.SetConsoleTextAttribute(_stdout, DEFAULT)


def color_print(*args, **kwargs) -> None:
    text = " ".join(str(arg) for arg in args)
    color = _color_for_text(text)
    if color:
        set_color(color)
    try:
        _original_print(*args, **kwargs)
    finally:
        if color:
            reset_color()


def _color_for_text(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped.startswith("[ERRO]") or stripped.startswith("ERRO:"):
        return "red"
    if stripped.startswith("[AVISO]") or stripped.startswith("[PULADO]"):
        return "yellow"
    if stripped.startswith("[OK]") or "Concluido." in stripped:
        return "green"
    if stripped.startswith("[") and "]" in stripped:
        return "cyan"
    if re.fullmatch(r"=+", stripped):
        return "cyan"
    if stripped.startswith("  ") and not stripped.startswith("   "):
        return "white"
    if stripped.startswith("Encoder:"):
        return "green"
    return None


def enable_colors() -> None:
    global _enabled
    if _enabled:
        return
    builtins.print = color_print
    _enabled = True
