from pathlib import Path

# We wrap each command as a convenient way to customize CLI docs and to make
# all imports lazy, since some of these actions have a lot of dependencies.


def convert_to_md(md_path: Path) -> None:
    """
    Convert a docx file to clean Markdown, hopefully in good enough shape
    to publish. Uses MarkItDown/Mammoth/Markdownify and a few additional
    cleanups and flowmark clean Markdown formatting.
    This works well to convert docx files from Gemini Deep Research
    output: click to export a report to Google Docs, then select `File >
    Download > Microsoft Word (.docx)`.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_convert_to_md import textpress_convert_to_md

    input = prepare_action_input(md_path)
    textpress_convert_to_md(input.items[0])


def format(md_path: Path) -> None:
    """
    Convert and format text, Markdown, or an HTML fragment to pretty, formatted,
    minified HTML using the TextPress template. Supports GFM-flavored Markdown
    tables and footnotes.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_format import textpress_format

    input = prepare_action_input(md_path)
    textpress_format(input.items[0])


def publish(path: Path) -> None:
    """
    Publish a document as a Textpress webpage. Converts from docx, Markdown, or
    HTML, renders, minifies, and publishes the result.
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
