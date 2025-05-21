from kash.actions.core.markdownify import markdownify
from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_fullpage_html_body,
    has_html_body,
    has_markdown_body,
    has_markdown_with_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_pdf_resource,
    is_url_resource,
)
from kash.kits.docs.actions.text.docx_to_md import docx_to_md
from kash.kits.docs.actions.text.endnotes_to_footnotes import endnotes_to_footnotes
from kash.model import ActionInput, ActionResult
from kash.utils.errors import InvalidInput

from texpr.docs.doc_cleanups import gemini_cleanups

log = get_logger(__name__)


@kash_action(
    precondition=is_url_resource
    | is_docx_resource
    | is_pdf_resource
    | has_html_body
    | has_markdown_body
    | has_markdown_with_html_body
    | has_simple_text_body
)
def textpress_convert(input: ActionInput) -> ActionResult:
    item = input.items[0]

    if is_url_resource(item) or has_fullpage_html_body(item):
        # Web formats should be converted to Markdown.
        result_item = markdownify(item)

    elif is_docx_resource(item):
        # First do basic conversion to markdown.
        md_item = docx_to_md(item)

        # Cleanups for Gemini reports. Should be fine on other files too.
        assert md_item.body
        md_item.body = gemini_cleanups(md_item.body)
        result_item = endnotes_to_footnotes(md_item)
    elif (
        has_markdown_body(item)
        or has_markdown_with_html_body(item)
        or has_html_body(item)
        or has_simple_text_body(item)
    ):
        log.message("Document already in Markdown so not converting")
        result_item = item
    else:
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    return ActionResult(items=[result_item])
