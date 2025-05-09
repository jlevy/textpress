"""
Convert, edit, and publish content in Textpress.

More information: https://github.com/jlevy/texpr
"""

import argparse
import logging
import sys
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent

from kash.shell.utils.argparse_utils import WrappedColorFormatter
from prettyfmt import fmt_path
from rich import print as rprint

from texpr.cli_commands import (
    convert_to_md,
    publish,
    reformat_md,
    render_webpage,
)

log = logging.getLogger(__name__)

APP_NAME = "texpr"

DESCRIPTION = """Textpress: Simple publishing for complex ideas"""

DEFAULT_WORK_ROOT = Path("./textpress")


COMMANDS = [
    "reformat_md",
    "docx_to_md",
    "render_as_html",
    "format_gemini_report",
    "publish",
]


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=WrappedColorFormatter,
        epilog=dedent((__doc__ or "") + "\n\n" + f"{APP_NAME} {get_app_version()}"),
        description=DESCRIPTION,
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {get_app_version()}")

    # Common arguments for all actions.
    parser.add_argument(
        "--work_dir",
        type=str,
        default=DEFAULT_WORK_ROOT,
        help="work directory to use for workspace, logs, and cache",
    )
    parser.add_argument(
        "--rerun", action="store_true", help="rerun actions even if the outputs already exist"
    )

    # Parsers for each command.
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparser = subparsers.add_parser(
        "reformat_md",
        help=reformat_md.__doc__,
        description=reformat_md.__doc__,
        formatter_class=WrappedColorFormatter,
    )
    subparser.add_argument("input_path", type=str, help="Input file (use '-' for stdin)")
    subparser.add_argument(
        "-o",
        "--output",
        type=str,
        default="-",
        help="Output file (use '-' for stdout)",
    )

    for func in [
        convert_to_md,
        render_webpage,
        publish,
    ]:
        subparser = subparsers.add_parser(
            func.__name__,
            help=func.__doc__,
            description=func.__doc__,
            formatter_class=WrappedColorFormatter,
        )
        subparser.add_argument("input_path", type=str, help="Path to the input file")

    return parser


def run_workspace_command(subcommand: str, args: argparse.Namespace) -> int:
    # Lazy imports! Can be slow so only do for processing commands.
    import kash.exec  # noqa: F401  # pyright: ignore
    from kash.config.logger import get_log_settings
    from kash.config.setup import kash_setup
    from kash.workspaces import get_ws, switch_to_ws

    # Now kash/workspace commands.
    # Have kash use textpress workspace.
    ws_root = Path(args.work_dir).resolve()
    ws_path = ws_root / "workspace"

    # Set up kash workspace root.
    kash_setup(rich_logging=True, kash_ws_root=ws_root)

    # Get the workspace.
    ws = get_ws(ws_path)
    log.warning("Switching to workspace: %s", ws.base_dir)
    switch_to_ws(ws.base_dir)

    # Show the user the workspace info.
    ws.log_workspace_info()

    # Run actions in the context of this workspace.
    with ws:
        log.info("Running action: %s", args.subcommand)

        # Handle each command.
        try:
            input_path = Path(args.input_path)
            if subcommand == reformat_md.__name__:
                reformat_md(input_path, args.output)
            elif subcommand == convert_to_md.__name__:
                convert_to_md(input_path)
            elif subcommand == render_webpage.__name__:
                render_webpage(input_path)
            elif subcommand == publish.__name__:
                publish(Path(args.input_path))
            else:
                raise ValueError(f"Unknown subcommand: {args.subcommand}")

        except Exception as e:
            log.error("Error running action: %s: %s", subcommand, e)
            log.info("Error details", exc_info=e)
            log_file = get_log_settings().log_file_path
            rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
            return 1

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # As a convenience also allow dashes in the subcommand name.
    subcommand = args.subcommand.replace("-", "_")

    sys.exit(run_workspace_command(subcommand, args))


if __name__ == "__main__":
    main()
