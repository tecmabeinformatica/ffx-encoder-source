from __future__ import annotations

import itertools
import subprocess
import sys
import time
from pathlib import Path


def _short_label(label: str, max_length: int = 90) -> str:
    if len(label) <= max_length:
        return label
    return label[: max_length - 3] + "..."


def run_with_spinner(args: list[str | Path], label: str) -> int:
    display_label = _short_label(label)
    frames = itertools.cycle("|/-\\")
    process = subprocess.Popen(
        [str(arg) for arg in args],
        stdout=subprocess.DEVNULL,
        stderr=None,
    )

    try:
        while process.poll() is None:
            frame = next(frames)
            sys.stdout.write(f"\r{display_label}  Processando... {frame}")
            sys.stdout.flush()
            time.sleep(0.08)

        exit_code = process.wait()
    finally:
        if process.poll() is None:
            process.kill()

    status = "Concluido." if exit_code == 0 else "Erro."
    sys.stdout.write(f"\r{display_label}  {status}                          \n")
    sys.stdout.flush()
    return exit_code


def run_with_percent(args: list[str | Path], label: str, duration_seconds: float) -> int:
    if duration_seconds <= 0:
        return run_with_spinner(args, label)

    display_label = _short_label(label)
    frames = itertools.cycle("|/-\\")
    command = [str(arg) for arg in args]
    if len(command) >= 2:
        command = [*command[:-1], "-stats_period", "0.2", "-progress", "pipe:1", command[-1]]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    last_percent = 0
    last_frame_time = 0.0

    try:
        while process.poll() is None:
            line = process.stdout.readline() if process.stdout else ""
            now = time.monotonic()

            if line:
                key, _, value = line.strip().partition("=")
                if key in {"out_time_ms", "out_time_us"} and value.isdigit():
                    seconds_done = int(value) / 1_000_000
                    percent = int((seconds_done / duration_seconds) * 100)
                    last_percent = max(last_percent, min(percent, 100))

            if now - last_frame_time >= 0.08:
                frame = next(frames)
                sys.stdout.write(f"\r{display_label}  {last_percent}%  {frame}")
                sys.stdout.flush()
                last_frame_time = now

        exit_code = process.wait()
    finally:
        if process.poll() is None:
            process.kill()

    status = "100%" if exit_code == 0 else "Erro."
    sys.stdout.write(f"\r{display_label}  {status}                          \n")
    sys.stdout.flush()
    return exit_code
