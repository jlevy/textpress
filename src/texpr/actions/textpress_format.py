from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_full_html_page_body,
    has_text_body,
    is_docx_resource,
    is_html,
)
from kash.kits.docs.actions.text.minify_html import minify_html
from kash.model import ONE_OR_MORE_ARGS, Format, Item, ItemType, Param
from kash.utils.errors import InvalidInput

from texpr.actions.textpress_convert import textpress_convert
from texpr.actions.textpress_render_template import textpress_render_template

log = get_logger(__name__)


@kash_action(
    expected_args=ONE_OR_MORE_ARGS,
    precondition=(is_docx_resource | is_html | has_text_body) & ~has_full_html_page_body,
    params=(Param("add_title", "Add a title to the page body.", type=bool),),
)
def textpress_format(item: Item, add_title: bool = False) -> Item:
    if is_html(item) or has_text_body(item):
        doc_item = item
    elif is_docx_resource(item):
        log.message("Converting docx to Markdown...")
        doc_item = textpress_convert(item)
    else:
        # TODO: Add PDF support.
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    html_item = textpress_render_template(doc_item, add_title=add_title)

    minified_item = minify_html(html_item)

    # Put the final formatted result as an export with the same title as the original.
    result_item = Item(
        type=ItemType.export, format=Format.html, title=item.abbrev_title(), body=minified_item.body
    )

    log.message("Formatted item: %s", result_item)

    return result_item
