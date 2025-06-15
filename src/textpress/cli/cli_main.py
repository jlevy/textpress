"""
The `textpress` (or `tp`) command lets you convert and format complex docs
(like Deep Research reports) to and from clean Markdown as well as
publish your content to Textpress.

For more information: https://textpress.md
"""

import argparse
import sys
import webbrowser
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent
from typing import Literal

from clideps.env_vars.env_enum import MissingEnvVar
from clideps.utils.readable_argparse import ReadableColorFormatter, get_readable_console_width
from kash.utils.common.url import Url, is_url
from prettyfmt import fmt_path
from rich import get_console
from rich import print as rprint

from textpress.api.textpress_api import get_user
from textpress.api.textpress_env import get_api_config
from textpress.cli.cli_commands import (
    convert,
    export,
    files,
    format,
    help,
    paste,
    publish,
    setup,
)

APP_NAME = "textpress"
KASH_SHELL = "kash-shell"
KASH_DOCS = "kash-docs"

DESCRIPTION = """Textpress: Simple publishing for complex docs"""


DEFAULT_WORK_ROOT = Path("./textpress")

ALL_COMMANDS = [help, setup, paste, files, convert, format, publish, export]

ACTION_COMMANDS = [convert, format, publish, export]


def get_version_name() -> str:
    try:
        textpress_version = version(APP_NAME)
        kash_version = version(KASH_SHELL)
        kash_docs_version = version(KASH_DOCS)
        return f"{APP_NAME} v{textpress_version} ({KASH_SHELL} v{kash_version}, {KASH_DOCS} v{kash_docs_version})"
    except Exception:
        return "(unknown version)"


def add_general_flags(parser: argparse.ArgumentParser) -> None:
    """
    These are flags that should work anywhere (main parser and subparsers).
    """
    parser.add_argument(
        "--debug", action="store_true", help="enable debug logging (log level: debug)"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="enable verbose logging (log level: info)"
    )
    parser.add_argument("--quiet", action="store_true", help="only log errors (log level: error)")


def add_action_flags(parser: argparse.ArgumentParser) -> None:
    """
    These are flags that work on kash actions.
    """
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="rerun actions even if the outputs already exist in the workspace",
    )
    parser.add_argument(
        "--refetch",
        action="store_true",
        help="refetch cached web or media content, even if it is already in the workspace cache",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        formatter_class=ReadableColorFormatter,
        epilog=dedent((__doc__ or "") + "\n\n" + get_version_name()),
        description=DESCRIPTION,
    )
    parser.add_argument("--version", action="version", version=get_version_name())

    # Common arguments for all actions.
    parser.add_argument(
        "--work_root",
        type=str,
        default=DEFAULT_WORK_ROOT,
        help=f"work directory root to use for workspace, logs, and cache directories (default: {DEFAULT_WORK_ROOT})",
    )
    # Add general flags to main parser
    add_general_flags(parser)

    # Parsers for each command.
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Add options for each command.
    for func in ALL_COMMANDS:
        subparser = subparsers.add_parser(
            func.__name__,
            help=func.__doc__,
            description=func.__doc__,
            formatter_class=ReadableColorFormatter,
        )
        add_general_flags(subparser)

        # Options for all actions:
        if func in ACTION_COMMANDS:
            add_action_flags(subparser)
            subparser.add_argument("input", type=str, help="Path or URL to the input file")

        # Options for convert command:
        if func in {convert}:
            subparser.add_argument(
                "--show",
                action="store_true",
                help="after it is complete, show the result in the console with a pager",
            )

        # Options for actions that produce HTML output:
        if func in {format, publish}:
            subparser.add_argument(
                "--show",
                action="store_true",
                help="after it is complete, open the result in your web browser",
            )
            subparser.add_argument(
                "--add_classes",
                type=str,
                default="",
                help="Space-delimited classes to add to the body of the page.",
            )
            subparser.add_argument(
                "--no_minify",
                action="store_true",
                help="Skip HTML/CSS/JS/Tailwind minification step.",
            )

        # `setup` options:
        if func in {setup}:
            subparser.add_argument(
                "--show",
                action="store_true",
                help="show the current config and environment variables",
            )

        # `files` options:
        if func in {files}:
            subparser.add_argument(
                "--all",
                action="store_true",
                help="show hidden and ignored files",
            )

        # `paste` options:
        if func in {paste}:
            subparser.add_argument(
                "--title",
                type=str,
                default="pasted_text",
                help="Title for the imported item (default: pasted_text)",
            )
            subparser.add_argument(
                "--plaintext",
                action="store_true",
                help="Treat input as plaintext instead of Markdown",
            )

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


_placehoder_username = "<your_username>"


def public_url_for(path: Path) -> Url:
    config = get_api_config()
    publish_root = config.publish_root
    username = get_user(config).username
    if not username.strip():
        raise ValueError("Username is not set (configuration error?)")
    filename = path.name
    if not filename.strip():
        raise ValueError("Filename missing")
    return Url(f"{publish_root}/{username}/d/{filename}")


def local_url_for(path: Path) -> Url:
    return Url(f"file://{path.resolve()}")


def open_url(url: Url) -> None:
    print(f"Opening browser: {url}")
    webbrowser.open(url)


def display_output(ws_path: Path, store_paths: list[Path], published_urls: list[Url]) -> None:
    rprint()
    rprint()
    rprint("[bold green]Success![/bold green]")
    rprint(f"[bright_black]Processed files in the workspace: {fmt_path(ws_path)}[/bright_black]")

    if store_paths:
        rprint()
        rprint("[bright_black]Results are now at:[/bright_black]")
        for path in store_paths:
            rprint(f"[bold cyan]{fmt_path(ws_path / path)}[/bold cyan]")

    if published_urls:
        rprint()
        rprint("[bright_black]Published URLs:[/bright_black]")
        for url in published_urls:
            rprint(f"[bold blue]{url}[/bold blue]")

    rprint()


def clean_class_names(classes_str: str) -> str:
    """
    Clean and normalize space or comma-separated class names and remove quotes.
    """
    classes_str = classes_str.strip("\"'")
    classes = [c.strip().strip("\"'") for c in classes_str.replace(",", " ").split()]
    return " ".join(classes)


def run_workspace_command(subcommand: str, args: argparse.Namespace) -> int:
    # Lazy imports! Can be slow so only do for processing commands.
    import httpx
    from kash.commands.base.show_command import show
    from kash.config.logger import CustomLogger, get_log_settings, get_logger
    from kash.config.setup import kash_setup
    from kash.exec import kash_runtime
    from kash.model import ActionResult, Format

    from textpress.cli.cli_setup import load_env

    log: CustomLogger = get_logger(__name__)

    # Load the environment variables (from all possible sources).
    load_env()

    # Now kash/workspace commands.
    # Have kash use textpress workspace.
    ws_root = Path(args.work_root).resolve()
    ws_path = ws_root / "workspace"

    # Set up kash workspace root.
    kash_setup(rich_logging=True, kash_ws_root=ws_root, console_log_level=get_log_level(args))

    log.info("Textpress config: %s", get_api_config())

    rerun = getattr(args, "rerun", False)
    refetch = getattr(args, "refetch", False)

    # Run actions in the context of this workspace.
    with kash_runtime(ws_path, rerun=rerun, refetch=refetch) as runtime:
        # Show the user the workspace info.
        runtime.workspace.log_workspace_info()

        # Handle each command.
        log.info("Running subcommand: %s", args.subcommand)
        store_paths: list[Path] = []
        published_urls: list[Url] = []
        try:
            result: ActionResult
            if subcommand == paste.__name__:
                store_path = paste(args.title, plaintext=args.plaintext)
                store_paths.append(store_path)
            elif subcommand == files.__name__:
                files(all=args.all)
            else:
                # Commands with a single input path and store path outputs.
                input = Url(args.input) if is_url(args.input) else Path(args.input)
                if subcommand == convert.__name__:
                    result = convert(input)
                    assert result.items[0].store_path
                    store_paths.append(Path(result.items[0].store_path))

                    if args.show:
                        # Show the converted file using kash show command
                        show(str(ws_path / Path(result.items[0].store_path)), console=True)
                elif subcommand == format.__name__:
                    result = format(
                        input,
                        add_classes=clean_class_names(args.add_classes),
                        no_minify=args.no_minify,
                    )

                    md_item = result.get_by_format(Format.markdown, Format.md_html)
                    html_item = result.get_by_format(Format.html)
                    assert md_item.store_path and html_item.store_path

                    store_paths.extend([Path(md_item.store_path), Path(html_item.store_path)])

                    local_url = local_url_for(path=ws_path / Path(html_item.store_path))
                    if args.show:
                        open_url(local_url)
                elif subcommand == publish.__name__:
                    result = publish(
                        input,
                        add_classes=clean_class_names(args.add_classes),
                        no_minify=args.no_minify,
                    )

                    md_item = result.get_by_format(Format.markdown, Format.md_html)
                    html_item = result.get_by_format(Format.html)
                    assert md_item.store_path and html_item.store_path

                    md_url = public_url_for(ws_path / Path(md_item.store_path).name)
                    html_url = public_url_for(ws_path / Path(html_item.store_path).name)

                    store_paths.extend([Path(md_item.store_path), Path(html_item.store_path)])
                    published_urls.extend([md_url, html_url])
                    if args.show and _placehoder_username not in html_url:
                        webbrowser.open(html_url)
                elif subcommand == export.__name__:
                    result = export(input)

                    docx_item = result.get_by_format(Format.docx)
                    pdf_item = result.get_by_format(Format.pdf)
                    assert docx_item.store_path and pdf_item.store_path

                    store_paths.extend([Path(docx_item.store_path), Path(pdf_item.store_path)])
                else:
                    raise ValueError(f"Unknown subcommand: {args.subcommand}")

            if store_paths or published_urls:
                display_output(ws_path, store_paths, published_urls)

        except MissingEnvVar as e:
            rprint()
            log.error("Missing environment variable: %s", e)
            rprint()
            rprint("Run `[bold cyan]textpr setup[/bold cyan]` to set up your API key.")
            return 1
        except httpx.HTTPStatusError as e:
            rprint()
            log.error("HTTP error: status %s: %s", e.response.status_code, e.request.url)
            rprint()
            return 1
        except KeyboardInterrupt:
            rprint()
            log.warning("[yellow]Cancelled[/yellow]")
            rprint()
            return 130
        except Exception as e:
            rprint()
            log.error("Error running action: %s: %s: %s", subcommand, e.__class__.__name__, e)
            log.info("Error details", exc_info=e)
            log_file = get_log_settings().log_file_path
            rprint(f"[bright_black]See logs for more details: {fmt_path(log_file)}[/bright_black]")
            return 2

    return 0


def main() -> None:
    get_console().width = get_readable_console_width()
    parser = build_parser()
    args = parser.parse_args()

    # As a convenience also allow dashes in the subcommand name.
    subcommand = args.subcommand.replace("-", "_")

    if subcommand == setup.__name__:
        setup(show=args.show)
        return
    elif subcommand == help.__name__:
        help()
        return

    sys.exit(run_workspace_command(subcommand, args))


if __name__ == "__main__":
    main()
