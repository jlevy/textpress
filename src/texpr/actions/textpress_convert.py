from kash.actions.core.markdownify import markdownify
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_full_html_page_body,
    has_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_url_resource,
)
from kash.kits.docs.actions.text.docx_to_md import docx_to_md
from kash.kits.docs.actions.text.endnotes_to_footnotes import endnotes_to_footnotes
from kash.model import ActionInput, ActionResult
from kash.utils.errors import InvalidInput

from texpr.doc_cleanups import gemini_cleanups


@kash_action(
    precondition=is_url_resource
    | is_docx_resource
    | has_html_body
    | has_simple_text_body & ~has_full_html_page_body
)
def textpress_convert(input: ActionInput) -> ActionResult:
    item = input.items[0]
    if is_url_resource(item):
        result_item = markdownify(item)
    elif has_html_body(item) or has_simple_text_body(item):
        result_item = item
    elif is_docx_resource(item):
        # First do basic conversion to markdown.
        md_item = docx_to_md(item)

        # Cleanups for Gemini reports. Should be fine on other files too.
        assert md_item.body
        md_item.body = gemini_cleanups(md_item.body)
        result_item = endnotes_to_footnotes(md_item)
    else:
        # TODO: Add PDF support.
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    return ActionResult(items=[result_item])
