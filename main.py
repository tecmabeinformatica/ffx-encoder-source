import sys
from pathlib import Path

from ffx_encoder.menu import run_main_menu


def main() -> None:
    work_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    run_main_menu(work_dir)


if __name__ == "__main__":
    main()
