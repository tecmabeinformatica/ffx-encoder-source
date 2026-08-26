from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from .config import AppConfig


TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"


def _read_config_token(paths: list[Path]) -> str:
    keys = ("tmdb_read_token", "read_token", "api_read_token", "token")
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", ";")) or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip().lower() in keys and value.strip():
                return value.strip()
    return ""


def _decrypt_ffx_dat(path: Path) -> str:
    safe_path = str(path).replace("'", "''")
    script = f"""
$DataPath = '{safe_path}'
$key=[Text.Encoding]::UTF8.GetBytes('FFXEnc0derTok3nKey-2026-Secret!!')
$iv=[Text.Encoding]::UTF8.GetBytes('DjManecaFFX2026!')
$bytes=[Convert]::FromBase64String((Get-Content -LiteralPath $DataPath -Raw).Trim())
$aes=[Security.Cryptography.Aes]::Create()
$aes.Key=$key; $aes.IV=$iv; $aes.Mode='CBC'; $aes.Padding='PKCS7'
$plain=$aes.CreateDecryptor().TransformFinalBlock($bytes,0,$bytes.Length)
[Text.Encoding]::UTF8.GetString($plain).Trim()
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def get_tmdb_token(work_dir: Path) -> str:
    config = AppConfig()
    token_sources = [
        ("dat", config.app_root / "ffx.dat"),
        ("config", config.app_root / "ffx.config"),
        ("config", config.app_root / "tmdb.ini"),
        ("dat", work_dir / "ffx.dat"),
        ("config", work_dir / "ffx.config"),
        ("config", work_dir / "tmdb.ini"),
        ("dat", Path(r"C:\FFmpeg\ffx.dat")),
        ("config", Path(r"C:\FFmpeg\ffx.config")),
        ("config", Path(r"C:\FFmpeg\tmdb.ini")),
    ]
    for source_type, path in token_sources:
        if path.exists():
            token = _decrypt_ffx_dat(path) if source_type == "dat" else _read_config_token([path])
            if token:
                return token

    raise FileNotFoundError("Token TMDb nao encontrado em ffx.dat, ffx.config ou tmdb.ini.")


def tmdb_get(path: str, work_dir: Path, params: dict[str, str] | None = None) -> dict:
    token = get_tmdb_token(work_dir)
    query = urllib.parse.urlencode(params or {})
    url = f"https://api.themoviedb.org/3{path}"
    if query:
        url += f"?{query}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def search_multi(query: str, work_dir: Path) -> list[dict]:
    data = tmdb_get(
        "/search/multi",
        work_dir,
        {"query": query, "language": "pt-BR", "include_adult": "false", "page": "1"},
    )
    return [
        item
        for item in data.get("results", [])[:8]
        if item.get("media_type") in {"movie", "tv"} and item.get("poster_path")
    ]


def search_movies(query: str, work_dir: Path) -> list[dict]:
    data = tmdb_get(
        "/search/movie",
        work_dir,
        {"query": query, "language": "pt-BR", "include_adult": "false", "page": "1"},
    )
    return [item for item in data.get("results", [])[:8] if item.get("poster_path")]


def season_details(tv_id: int, season_number: int, work_dir: Path) -> dict:
    return tmdb_get(f"/tv/{tv_id}/season/{season_number}", work_dir, {"language": "pt-BR"})


def download_poster(poster_path: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{TMDB_IMAGE_BASE}{poster_path}", destination)
