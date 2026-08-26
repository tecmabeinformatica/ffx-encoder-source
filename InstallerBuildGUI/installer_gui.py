from __future__ import annotations

import sys
import winreg
import zipfile
from pathlib import Path


APP_NAME = "FFX Encoder GUI"
PAYLOAD_NAME = "FFX Encoder GUI Payload.zip"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FFX Encoder GUI"


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def set_reg_value(root, path: str, name: str | None, value: str) -> None:
    with winreg.CreateKey(root, path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def install_context_menu(exe_path: Path) -> None:
    label = "Abrir com FFX Encoder GUI"
    icon_value = f'"{exe_path}"'
    command_background = f'"{exe_path}" "%V"'
    command_folder = f'"{exe_path}" "%1"'

    base_background = r"Software\Classes\Directory\Background\shell\FFX Encoder GUI"
    base_folder = r"Software\Classes\Directory\shell\FFX Encoder GUI"

    set_reg_value(winreg.HKEY_CURRENT_USER, base_background, None, label)
    set_reg_value(winreg.HKEY_CURRENT_USER, base_background, "Icon", icon_value)
    set_reg_value(winreg.HKEY_CURRENT_USER, base_background + r"\command", None, command_background)

    set_reg_value(winreg.HKEY_CURRENT_USER, base_folder, None, label)
    set_reg_value(winreg.HKEY_CURRENT_USER, base_folder, "Icon", icon_value)
    set_reg_value(winreg.HKEY_CURRENT_USER, base_folder + r"\command", None, command_folder)


def install_uninstall_entry(install_root: Path, exe_path: Path) -> None:
    uninstall_path = install_root / "Desinstalar FFX Encoder GUI.bat"
    set_reg_value(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, "DisplayName", APP_NAME)
    set_reg_value(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, "DisplayVersion", "2.0 Final")
    set_reg_value(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, "Publisher", "DjManeca")
    set_reg_value(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, "InstallLocation", str(install_root))
    set_reg_value(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, "DisplayIcon", str(exe_path))
    set_reg_value(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY, "UninstallString", f'"{uninstall_path}"')


def main() -> int:
    payload = resource_path(PAYLOAD_NAME)
    install_root = Path(r"C:\FFX Encoder GUI")
    exe_path = install_root / "FFX Encoder GUI.exe"

    print("=========================================================")
    print("  INSTALANDO FFX ENCODER GUI")
    print("=========================================================")
    print()

    if not payload.exists():
        print(f"[ERRO] Pacote interno nao encontrado: {payload}")
        input("\nPressione ENTER para sair...")
        return 1

    print("Extraindo arquivos...")
    install_root.mkdir(parents=True, exist_ok=True)
    legacy_token = install_root / "ffx.dat"
    if legacy_token.exists():
        legacy_token.unlink()
    with zipfile.ZipFile(payload, "r") as zip_file:
        zip_file.extractall(install_root)

    print("Registrando desinstalador...")
    install_uninstall_entry(install_root, exe_path)

    print("Instalando menu de contexto separado...")
    install_context_menu(exe_path)

    print()
    print("[OK] Instalacao concluida.")
    print(f"Pasta instalada: {install_root}")
    print("Esta versao grafica e independente da versao console.")
    print()
    input("Pressione ENTER para sair...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
