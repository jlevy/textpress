import logging

from kash.exec import kash_action
from kash.exec.preconditions import (
    has_text_body,
    is_docx_resource,
    is_html,
)
from kash.model import ONE_OR_MORE_ARGS, Format, Item, ItemType, Param

from texpr.actions.textpress_format import textpress_format
from texpr.textpress_api import publish_files

log = logging.getLogger(__name__)


@kash_action(
    expected_args=ONE_OR_MORE_ARGS,
    precondition=is_docx_resource | is_html | has_text_body,
    params=(Param("add_title", "Add the document title to the page body.", type=bool),),
    cacheable=False,
)
def textpress_publish(item: Item, add_title: bool = False) -> Item:
    """
    Publish a document as a Textpress webpage. Converts from docx, Markdown, or
    HTML, renders, minifies, and publishes the result.
    """
    rendered_item = textpress_format(item, add_title=add_title)

    manifest = publish_files([rendered_item.absolute_path()])
    files = manifest.files.keys()
    log.warning("Published: %s", files)

    result_item = rendered_item.derived_copy(type=ItemType.export, format=Format.html)
    return result_item
