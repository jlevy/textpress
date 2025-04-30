from kash.actions.core.render_as_html import render_as_html
from kash.exec import kash_action
from kash.exec.preconditions import is_docx_resource
from kash.kits.media.actions.text.docx_to_md import docx_to_md
from kash.kits.media.actions.text.endnotes_to_footnotes import endnotes_to_footnotes
from kash.model import ActionInput, Item


@kash_action(precondition=is_docx_resource)
def format_gemini_report(item: Item) -> Item:
    """
    Format the docx export of a Gemini research report as clean, ready-to-publish
    HTML.
    """
    # First do basic conversion to markdown.
    md_item = docx_to_md(item)

    # Gemini reports use superscripts with a long list of numeric references.
    # This converts them to proper footnotes.
    footnotes_item = endnotes_to_footnotes(md_item)

    # Finally render.
    result = render_as_html(ActionInput(items=[footnotes_item]))

    return result.items[0]
