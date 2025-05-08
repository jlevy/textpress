import logging
from pathlib import Path

log = logging.getLogger(__name__)


# We wrap each command as a convenient way to customize CLI docs and to make
# all imports lazy, since some of these actions have a lot of dependencies.


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


def docx_to_md(docx_path: Path) -> None:
    """
    Convert a docx file to clean Markdown, hopefully in good enough shape
    to publish. Uses MarkItDown/Mammoth/Markdownify and a few additional
    cleanups.

    This works well to convert docx files from Gemini Deep Research
    output: click to export a report to Google Docs, then select `File >
    Download > Microsoft Word (.docx)`.
    """
    from kash.exec import prepare_action_input
    from kash.kits.docs.actions.text.docx_to_md import docx_to_md

    input = prepare_action_input(docx_path)
    docx_to_md(input.items[0])


def render_as_html(md_path: Path) -> None:
    """
    Convert text, Markdown, or HTML to pretty, formatted HTML using the kash default
    page template.
    """
    from kash.actions.core.render_as_html import render_as_html
    from kash.exec import prepare_action_input

    input = prepare_action_input(md_path)
    render_as_html(input)


def format_gemini_report(md_path: Path) -> None:
    """
    Format the docx export from Google Docs of a Gemini Deep Research report
    as clean, ready-to-publish HTML.

    Handles interpretation of superscripts as footnote citations
    and other document cleanup to make the report much more readable and
    the Markdown intermediate representation clean and useful.
    """
    from kash.exec import prepare_action_input
    from kash.kits.docs.actions.text.format_gemini_report import format_gemini_report

    input = prepare_action_input(md_path)
    format_gemini_report(input.items[0])


def publish(paths: list[Path]) -> None:
    """
    Publishes a list of files to Textpress.
    """
    import httpx

    from texpr.textpress_api import publish_files

    try:
        manifest = publish_files(paths)
        files = manifest.files.keys()
        log.warning("Published %d files: %s", len(files), ", ".join(files))
    except (httpx.HTTPStatusError, ValueError, FileNotFoundError) as e:
        # Catch specific, expected errors.
        log.exception("Publishing failed: %s", e)
    except Exception as e:
        log.exception("An unexpected error occurred during publishing: %s", e)
