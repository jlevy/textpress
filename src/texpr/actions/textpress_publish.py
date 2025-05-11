from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_text_body,
    is_docx_resource,
    is_html,
)
from kash.model import ONE_OR_MORE_ARGS, Format, Item, ItemType, Param
from kash.workspaces import current_ws

from texpr.actions.textpress_format import textpress_format
from texpr.textpress_api import publish_files

log = get_logger(__name__)


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
    formatted_item = textpress_format(item, add_title=add_title)

    # Put the final result as an export with the same title as the original.
    result_item = Item(
        type=ItemType.export,
        format=Format.html,
        title=item.abbrev_title(),  # Pull title from original item.
        body=formatted_item.body,
    )

    current_ws().save(result_item)

    log.message("Item is ready to publish: %s", result_item)

    manifest = publish_files([result_item.absolute_path()])

    files = manifest.files.keys()
    log.message("Published: %s", files)

    return result_item
