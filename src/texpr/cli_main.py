"""
Convert, edit, and publish content in Textpress.

More information: https://github.com/jlevy/texpr
"""

import argparse
import sys
import webbrowser
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent
from typing import Literal

from clideps.utils.readable_argparse import ReadableColorFormatter
from kash.utils.common.url import Url
from prettyfmt import fmt_path
from rich import print as rprint

from texpr.cli_commands import (
    convert,
    format,
    publish,
)
from texpr.textpress_env import Env

APP_NAME = "texpr"

DESCRIPTION = """Textpress: Simple publishing for complex ideas"""

DEFAULT_WORK_ROOT = Path("./textpress")


def get_app_version() -> str:
    try:
        return "v" + version(APP_NAME)
    except Exception:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=ReadableColorFormatter,
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

    for func in [
        convert,
        format,
        publish,
    ]:
        subparser = subparsers.add_parser(
            func.__name__,
            help=func.__doc__,
            description=func.__doc__,
            formatter_class=ReadableColorFormatter,
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


def display_output(ws_path: Path, store_paths: list[Path], published_urls: list[Url]) -> None:
    rprint()
    rprint()
    rprint("[bold green]Success![/bold green]")
    rprint(f"[bright_black]Processed files in the workspace: {fmt_path(ws_path)}[/bright_black]")
    rprint("[bright_black]Results is now at:[/bright_black]")
    rprint()
    if store_paths:
        rprint("[bright_black]Files saved to workspace:[/bright_black]")
        for path in store_paths:
            rprint(f"[bold cyan]{fmt_path(ws_path / path)}[/bold cyan]")
    if store_paths and published_urls:
        rprint()
    if published_urls:
        rprint("[bright_black]Published URLs:[/bright_black]")
        for url in published_urls:
            rprint(f"[bold blue]{url}[/bold blue]")


def run_workspace_command(subcommand: str, args: argparse.Namespace) -> int:
    # Lazy imports! Can be slow so only do for processing commands.
    from kash.config.logger import CustomLogger, get_log_settings, get_logger
    from kash.config.setup import kash_setup
    from kash.exec import kash_runtime
    from kash.model import Item

    log: CustomLogger = get_logger(__name__)

    # Now kash/workspace commands.
    # Have kash use textpress workspace.
    ws_root = Path(args.work_dir).resolve()
    ws_path = ws_root / "workspace"

    # Set up kash workspace root.
    kash_setup(rich_logging=True, kash_ws_root=ws_root, console_log_level=get_log_level(args))

    # Run actions in the context of this workspace.
    with kash_runtime(ws_path, rerun=args.rerun) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        # Handle each command.
        log.info("Running subcommand: %s", args.subcommand)
        published_urls: list[Url] = []
        try:
            input_path = Path(args.input_path)
            output_item: Item
            if subcommand == convert.__name__:
                output_item = convert(input_path)
            elif subcommand == format.__name__:
                output_item = format(input_path)
            elif subcommand == publish.__name__:
                output_item = publish(Path(args.input_path))

                publish_root = Env.TEXTPRESS_PUBLISH_ROOT.read_str(default="https://texpr.com")
                username = Env.TEXTPRESS_USERNAME.read_str(default=None)
                assert output_item.store_path
                filename = Path(output_item.store_path).name
                if username:
                    published_url = Url(f"{publish_root}/{username}/d/{filename}")
                else:
                    published_url = Url(f"{publish_root}/d/{filename}")
                published_urls.append(published_url)

                if publish_root and username:
                    webbrowser.open(published_url)
            else:
                raise ValueError(f"Unknown subcommand: {args.subcommand}")

            assert output_item.store_path
            display_output(ws_path, [Path(output_item.store_path)], published_urls)

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
