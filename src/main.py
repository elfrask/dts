import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    if len(sys.argv) > 1:
        from src.cli.cli import cli_main
        cli_main()
    else:
        from src.gui.app import gui_main
        gui_main()


if __name__ == "__main__":
    main()
