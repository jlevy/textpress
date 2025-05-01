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

from flowmark import reformat_file
from kash.actions.core.render_as_html import render_as_html
from kash.config.logger import get_log_settings
from kash.config.setup import kash_setup
from kash.exec import prepare_action_input
from kash.kits.docs.actions.text.docx_to_md import docx_to_md
from kash.kits.docs.actions.text.format_gemini_report import format_gemini_report
from kash.shell.utils.argparse_utils import WrappedColorFormatter
from kash.workspaces import get_ws
from kash.workspaces.workspaces import switch_to_ws
from prettyfmt import fmt_path
from rich import print as rprint

log = logging.getLogger(__name__)

APP_NAME = "texpr"

DESCRIPTION = """Textpress: Simple publishing for complex ideas"""

DEFAULT_WORK_ROOT = Path("./textpress")


CLI_ACTIONS = [
    docx_to_md,
    render_as_html,
    format_gemini_report,
]


def reformat_md(
    md_path: Path,
    output: Path | None,
    width: int = 88,
    semantic: bool = True,
    nobackup: bool = False,
) -> None:
    """
    Auto-format a markdown file. Uses flowmark to do readable line wrapping and
    Markdown-aware cleanups.
    """
    inplace = output is None
    reformat_file(
        md_path, output, inplace=inplace, width=width, semantic=semantic, nobackup=nobackup
    )


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

    for func in CLI_ACTIONS:
        subparser = subparsers.add_parser(
            func.__name__,
            help=func.__doc__,
            description=func.__doc__,
            formatter_class=WrappedColorFormatter,
        )
        subparser.add_argument("input_path", type=str, help="Path to the input file")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

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

        # As a convenience also allow dashes in the subcommand name.
        subcommand = args.subcommand.replace("-", "_")

        # Handle simple commands.
        if subcommand == "format_md":
            reformat_md(args.input_path, args.output)
            return

        # Handle kash actions.
        try:
            input = prepare_action_input(args.input_path)
            if subcommand == docx_to_md.__name__:
                docx_to_md(input.items[0])
            elif subcommand == render_as_html.__name__:
                render_as_html(input)
            elif subcommand == format_gemini_report.__name__:
                format_gemini_report(input.items[0])
            else:
                raise ValueError(f"Unknown subcommand: {args.subcommand}")

        except Exception as e:
            log.error("Error running action: %s: %s", subcommand, e)
            log.info("Error details", exc_info=e)
            log_file = get_log_settings().log_file_path
            rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
            sys.exit(1)


if __name__ == "__main__":
    main()
