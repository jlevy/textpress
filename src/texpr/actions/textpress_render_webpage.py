import logging

from kash.exec import kash_action
from kash.exec.preconditions import (
    has_full_html_page_body,
    has_text_body,
    is_docx_resource,
    is_html,
)
from kash.model import ONE_OR_MORE_ARGS, Format, Item, ItemType, Param
from kash.utils.errors import InvalidInput

from texpr.actions.textpress_convert_to_md import textpress_convert_to_md
from texpr.render_webpage import render_webpage

log = logging.getLogger(__name__)


@kash_action(
    expected_args=ONE_OR_MORE_ARGS,
    precondition=(is_docx_resource | is_html | has_text_body) & ~has_full_html_page_body,
    params=(Param("add_title", "Add a title to the page body.", type=bool),),
)
def textpress_render_webpage(item: Item, add_title: bool = False) -> Item:
    """
    Convert text, Markdown, or an HTML fragment to pretty, formatted, minified HTML using
    a clean and simple page template. Supports GFM-flavored Markdown tables and footnotes.
    """

    if is_docx_resource(item):
        log.warning("Converting docx to Markdown...")
        doc_item = textpress_convert_to_md(item)
    elif is_html(item) or has_text_body(item):
        doc_item = item
    else:
        # TODO: Add PDF support.
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    # Render the HTML.
    html_body = render_webpage(doc_item, add_title_h1=add_title)
    html_item = doc_item.derived_copy(type=ItemType.export, format=Format.html, body=html_body)

    # FIXME: Turn on: Minify the HTML.
    # minified_item = minify_html(html_item)

    return html_item
