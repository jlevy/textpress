from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

# We wrap each command as a convenient way to customize CLI docs and to make
# all imports lazy, since some of these actions have a lot of dependencies.
if TYPE_CHECKING:
    from kash.model import Item


def convert(md_path: Path) -> Item:
    """
    Convert a document to clean Markdown.

    This works well to convert docx files, especially Gemini Deep Research
    output: click to export a report to Google Docs, then select `File >
    Download > Microsoft Word (.docx)`.

    Uses MarkItDown/Mammoth/Markdownify and a few additional cleanups to
    convert docx files and flowmark for clean Markdown formatting.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_convert import textpress_convert

    input = prepare_action_input(md_path)
    return textpress_convert(input.items[0])


def format(md_path: Path) -> Item:
    """
    Convert and format text, Markdown, or an HTML fragment to pretty, formatted,
    minified HTML using the TextPress template.

    Supports GFM-flavored Markdown tables and footnotes. Uses `convert` to convert
    docx files.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_format import textpress_format

    input = prepare_action_input(md_path)
    return textpress_format(input.items[0])


def publish(path: Path) -> Item:
    """
    Publish (or re-publish) a document as a Textpress webpage. Uses `format`
    to convert and format the content and publishes the result.
    """
    from kash.exec import prepare_action_input

    from texpr.actions.textpress_publish import textpress_publish

    input = prepare_action_input(path)
    return textpress_publish(input.items[0])
