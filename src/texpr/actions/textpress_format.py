from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_full_html_page_body,
    has_text_body,
    is_docx_resource,
    is_html,
)
from kash.kits.docs.actions.text.minify_html import minify_html
from kash.model import ONE_OR_MORE_ARGS, Item, Param
from kash.utils.errors import InvalidInput

from texpr.actions.textpress_convert_to_md import textpress_convert_to_md
from texpr.actions.textpress_render_template import textpress_render_template

log = get_logger(__name__)


@kash_action(
    expected_args=ONE_OR_MORE_ARGS,
    precondition=(is_docx_resource | is_html | has_text_body) & ~has_full_html_page_body,
    params=(Param("add_title", "Add a title to the page body.", type=bool),),
)
def textpress_format(item: Item, add_title: bool = False) -> Item:
    """
    Convert and format text, Markdown, or an HTML fragment to pretty, formatted,
    minified HTML using the TextPress template. Supports GFM-flavored Markdown
    tables and footnotes.
    """

    if is_html(item) or has_text_body(item):
        doc_item = item
    elif is_docx_resource(item):
        log.warning("Converting docx to Markdown...")
        doc_item = textpress_convert_to_md(item)
    else:
        # TODO: Add PDF support.
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    html_item = textpress_render_template(doc_item, add_title=add_title)

    minified_item = minify_html(html_item)

    return minified_item
