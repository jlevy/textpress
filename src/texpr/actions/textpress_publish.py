from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_text_body,
    is_docx_resource,
    is_html,
)
from kash.model import ONE_OR_MORE_ARGS, Format, Item, ItemType, Param
from kash.workspaces import current_ws
from prettyfmt import fmt_path

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
    formatted_item = textpress_format(item, add_title=add_title)

    manifest = publish_files([formatted_item.absolute_path()])

    log.message("Published: %s", list(manifest.files.keys()))

    # Save the manifest but return the actual document.
    manifest_item = Item(
        type=ItemType.config,
        format=Format.json,
        title=f"Textpress Manifest: {item.title}",
        body=manifest.model_dump_json(indent=2),
    )
    manifest_path = current_ws().save(manifest_item)
    log.message("Manifest saved: %s", fmt_path(manifest_path))

    return formatted_item
