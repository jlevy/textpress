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
from typing import Literal

from kash.shell.utils.argparse_utils import WrappedColorFormatter
from prettyfmt import fmt_path
from rich import print as rprint

from texpr.cli_commands import (
    convert_to_md,
    format,
    publish,
    reformat_md,
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
        "--rerun",
        action="store_true",
        help="rerun actions even if the outputs already exist in the workspace",
    )
    parser.add_argument(
        "--debug", action="store_true", help="enable debug logging (log level: debug)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="enable verbose logging (log level: info)"
    )
    parser.add_argument("--quiet", action="store_true", help="only log errors (log level: error)")

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
        format,
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


def get_log_level(args: argparse.Namespace) -> Literal["debug", "info", "warning", "error"]:
    if args.quiet:
        return "error"
    elif args.verbose:
        return "info"
    elif args.debug:
        return "debug"
    else:
        return "warning"


def run_workspace_command(subcommand: str, args: argparse.Namespace) -> int:
    # Lazy imports! Can be slow so only do for processing commands.
    from kash.config.logger import get_log_settings
    from kash.config.setup import kash_setup
    from kash.exec import kash_runtime

    # Now kash/workspace commands.
    # Have kash use textpress workspace.
    ws_root = Path(args.work_dir).resolve()
    ws_path = ws_root / "workspace"

    # Set up kash workspace root.
    log_level = get_log_level(args)
    kash_setup(rich_logging=True, kash_ws_root=ws_root, console_log_level=log_level)

    # Run actions in the context of this workspace.
    with kash_runtime(ws_path, rerun=args.rerun) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        # Handle each command.
        log.info("Running subcommand: %s", args.subcommand)
        try:
            input_path = Path(args.input_path)
            if subcommand == reformat_md.__name__:
                reformat_md(input_path, args.output)
            elif subcommand == convert_to_md.__name__:
                convert_to_md(input_path)
            elif subcommand == format.__name__:
                format(input_path)
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
