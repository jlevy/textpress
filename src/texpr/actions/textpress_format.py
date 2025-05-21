from kash.actions.core.markdownify import markdownify
from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_fullpage_html_body,
    has_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_url_resource,
)
from kash.kits.docs.actions.text.minify_html import minify_html
from kash.model import (
    ONE_ARG,
    TWO_ARGS,
    ActionInput,
    ActionResult,
    Format,
    ItemType,
    Param,
)
from kash.utils.errors import InvalidInput
from prettyfmt import fmt_lines

from texpr.actions.textpress_convert import textpress_convert
from texpr.actions.textpress_render_template import textpress_render_template

log = get_logger(__name__)


@kash_action(
    expected_args=ONE_ARG,
    expected_outputs=TWO_ARGS,
    precondition=(is_url_resource | is_docx_resource | has_html_body | has_simple_text_body)
    & ~has_fullpage_html_body,
    params=(
        Param("add_title", "Add a title to the page body.", type=bool),
        Param("add_classes", "Space-delimited classes to add to the body of the page.", type=str),
    ),
)
def textpress_format(
    input: ActionInput, add_title: bool = False, add_classes: str | None = None
) -> ActionResult:
    item = input.items[0]
    if is_url_resource(item):
        raw_text_item = markdownify(item)
    elif has_html_body(item) or has_simple_text_body(item):
        raw_text_item = item
    elif is_docx_resource(item):
        log.message("Converting docx to Markdown...")
        raw_text_item = textpress_convert(input).items[0]
    else:
        # TODO: Add PDF support.
        raise InvalidInput(f"Don't know how to convert item to HTML: {item.type}")

    # Export the text item with original title or the heading if we can get it from the body.
    title = item.title or raw_text_item.body_heading()
    text_item = raw_text_item.derived_copy(type=ItemType.export, title=title)

    raw_html_item = textpress_render_template(
        text_item, add_title=add_title, add_classes=add_classes
    )

    minified_item = minify_html(raw_html_item)

    # Put the final formatted result as an export with the same title as the original.
    html_item = raw_html_item.derived_copy(
        type=ItemType.export,
        format=Format.html,
        title=title,
        body=minified_item.body,
    )

    log.message("Formatted HTML item from text item:\n%s", fmt_lines([raw_text_item, html_item]))

    # Setting overwrite means we'll always pick the same output paths and
    # both .html and .md filenames will match.
    return ActionResult(items=[text_item, html_item], overwrite=True)
