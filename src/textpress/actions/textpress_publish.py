from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_pdf_resource,
    is_url_resource,
)
from kash.exec_model.args_model import TWO_ARGS
from kash.model import (
    ONE_ARG,
    ActionInput,
    ActionResult,
    Format,
    Item,
    ItemType,
    Param,
)
from kash.workspaces import current_ws
from prettyfmt import fmt_lines, fmt_path

from textpress.actions.textpress_format import textpress_format
from textpress.api.textpress_api import publish_files

log = get_logger(__name__)


@kash_action(
    expected_args=ONE_ARG,
    expected_outputs=TWO_ARGS,
    precondition=(
        is_url_resource | is_docx_resource | is_pdf_resource | has_html_body | has_simple_text_body
    ),
    params=(
        Param("add_title", "Add the document title to the page body.", type=bool),
        Param("add_classes", "Space-delimited classes to add to the body of the page.", type=str),
        Param("no_minify", "Skip HTML/CSS/JS/Tailwind minification step.", type=bool),
    ),
    cacheable=False,
)
def textpress_publish(
    input: ActionInput,
    add_title: bool = False,
    add_classes: str | None = None,
    no_minify: bool = False,
) -> ActionResult:
    item = input.items[0]
    format_result = textpress_format(
        input, add_title=add_title, add_classes=add_classes, no_minify=no_minify
    )
    md_item = format_result.get_by_format(Format.markdown, Format.md_html)
    html_item = format_result.get_by_format(Format.html)

    upload_paths = [md_item.absolute_path(), html_item.absolute_path()]
    log.message("Publishing files:\n%s", fmt_lines(upload_paths))

    manifest = publish_files(upload_paths)

    log.message("Published: %s", list(manifest.files.keys()))

    # Save the manifest so we have it but don't include it in the output.
    manifest_item = Item(
        type=ItemType.data,
        format=Format.json,
        title=f"Textpress Manifest: {item.title}",
        body=manifest.model_dump_json(indent=2),
    )
    manifest_path = current_ws().save(manifest_item)
    log.message("Manifest saved: %s", fmt_path(manifest_path))

    return ActionResult(items=[md_item, html_item])
