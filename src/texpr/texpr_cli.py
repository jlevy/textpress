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

from flowmark import first_sentence
from kash.actions.core.render_as_html import render_as_html
from kash.config.logger import get_log_settings
from kash.config.setup import kash_setup
from kash.exec import prepare_action_input
from kash.kits.media.actions.text.docx_to_md import docx_to_md
from kash.kits.media.actions.text.endnotes_to_footnotes import endnotes_to_footnotes
from kash.shell import shell_main
from kash.shell.utils.argparse_utils import WrappedColorFormatter
from kash.workspaces import get_ws
from kash.workspaces.workspaces import switch_to_ws
from prettyfmt import fmt_path
from rich import print as rprint

from texpr.format_gemini_report import format_gemini_report

log = logging.getLogger(__name__)

APP_NAME = "texpr"

DESCRIPTION = """Textpress: A simpler way to publish complex ideas"""

DEFAULT_WORK_ROOT = Path("./textpress")


CLI_ACTIONS = [
    docx_to_md,
    endnotes_to_footnotes,
    render_as_html,
    format_gemini_report,
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

    # Parsers for each action.
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    for func in CLI_ACTIONS:
        subparser = subparsers.add_parser(
            func.__name__,
            help=first_sentence(func.__doc__ or ""),
            description=func.__doc__,
            formatter_class=WrappedColorFormatter,
        )
        subparser.add_argument("input_path", type=str, help="Path to the input file")

    subparser = subparsers.add_parser(
        "kash",
        help="Launch the kash shell (a full command line environment with various tools loaded).",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Have kash use textpress workspace.
    ws_root = Path(args.work_dir).resolve()
    ws_path = ws_root / "workspace"

    # Set up kash workspace root.
    kash_setup(rich_logging=True, kash_ws_root=ws_root)

    # Option to run the kash shell with media tools loaded.
    if args.subcommand == "kash":
        rprint("[bright_black]Running kash shell with media tools loaded...[/bright_black]")
        sys.exit(shell_main.run_shell())

    # Get the workspace.
    ws = get_ws(ws_path)
    log.warning("Switching to workspace: %s", ws.base_dir)
    switch_to_ws(ws.base_dir)

    # Show the user the workspace info.
    ws.log_workspace_info()

    # Run actions in the context of this workspace.
    with ws:
        log.info("Running action: %s", args.subcommand)

        input = prepare_action_input(args.input_path)

        try:
            if args.subcommand == docx_to_md.__name__:
                docx_to_md(input.items[0])
            elif args.subcommand == endnotes_to_footnotes.__name__:
                endnotes_to_footnotes(input.items[0])
            elif args.subcommand == render_as_html.__name__:
                render_as_html(input)
            elif args.subcommand == format_gemini_report.__name__:
                format_gemini_report(input.items[0])
            else:
                raise ValueError(f"Unknown subcommand: {args.subcommand}")

        except Exception as e:
            log.error("Error running action: %s: %s", args.subcommand, e)
            log.info("Error details", exc_info=e)
            log_file = get_log_settings().log_file_path
            rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
            sys.exit(1)


if __name__ == "__main__":
    main()
