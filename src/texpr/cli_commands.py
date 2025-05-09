import logging
from pathlib import Path

log = logging.getLogger(__name__)


# We wrap each command as a convenient way to customize CLI docs and to make
# all imports lazy, since some of these actions have a lot of dependencies.


def convert_to_md(md_path: Path) -> None:
    """
    Convert a docx file to clean Markdown, hopefully in good enough shape
    to publish. Uses MarkItDown/Mammoth/Markdownify and a few additional
    cleanups.

    This works well to convert docx files from Gemini Deep Research
    output: click to export a report to Google Docs, then select `File >
    Download > Microsoft Word (.docx)`.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_convert_to_md import textpress_convert_to_md

    input = prepare_action_input(md_path)
    textpress_convert_to_md(input.items[0])


def render_webpage(md_path: Path) -> None:
    """
    Convert text, Markdown, or HTML to pretty, formatted HTML using the kash default
    page template.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_render_webpage import textpress_render_webpage

    input = prepare_action_input(md_path)
    textpress_render_webpage(input.items[0])


def publish(path: Path) -> None:
    """
    Publish a file to Textpress. Converts to markdown and HTML if necessary.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_publish import textpress_publish

    input = prepare_action_input(path)
    textpress_publish(input.items[0])


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
    from flowmark import reformat_file

    inplace = output is None
    reformat_file(
        md_path, output, inplace=inplace, width=width, semantic=semantic, nobackup=nobackup
    )
