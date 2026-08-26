from dataclasses import dataclass
from pathlib import Path
import sys


APP_NAME = "FFX Encoder"
APP_VERSION = "1.0 Final"
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", APP_ROOT))
LOCAL_FFMPEG_DIR = APP_ROOT / "bin"
BUNDLED_FFMPEG_DIR = BUNDLE_ROOT / "bin"
LOCAL_COVERS_DIR = APP_ROOT / "Capas"
DEFAULT_INSTALL_DIR = Path(r"C:\FFmpeg")
DEFAULT_FFMPEG_DIR = DEFAULT_INSTALL_DIR / "bin"
DEFAULT_COVERS_DIR = DEFAULT_INSTALL_DIR / "Capas"


@dataclass(frozen=True)
class AppConfig:
    app_name: str = APP_NAME
    version: str = APP_VERSION
    app_root: Path = APP_ROOT
    local_ffmpeg_dir: Path = LOCAL_FFMPEG_DIR
    bundled_ffmpeg_dir: Path = BUNDLED_FFMPEG_DIR
    local_covers_dir: Path = LOCAL_COVERS_DIR
    install_dir: Path = DEFAULT_INSTALL_DIR
    ffmpeg_dir: Path = DEFAULT_FFMPEG_DIR
    fallback_covers_dir: Path = DEFAULT_COVERS_DIR
