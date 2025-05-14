from kash.exec import kash_action
from kash.exec.preconditions import (
    has_full_html_page_body,
    has_simple_text_body,
    is_docx_resource,
    is_html,
)
from kash.kits.docs.actions.text.docx_to_md import docx_to_md
from kash.kits.docs.actions.text.endnotes_to_footnotes import endnotes_to_footnotes
from kash.model import ActionInput, ActionResult
from kash.utils.errors import InvalidInput


@kash_action(
    precondition=(is_docx_resource | is_html | has_simple_text_body) & ~has_full_html_page_body
)
def textpress_convert(input: ActionInput) -> ActionResult:
    item = input.items[0]
    if is_html(item) or has_simple_text_body(item):
        result_item = item
    elif is_docx_resource(item):
        # First do basic conversion to markdown.
        md_item = docx_to_md(item)

        # Gemini reports use superscripts with a long list of numeric references.
        # This converts them to proper footnotes. Should be safe for any doc.
        result_item = endnotes_to_footnotes(md_item)
    else:
        # TODO: Add PDF support.
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    return ActionResult(items=[result_item])
