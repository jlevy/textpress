from kash.actions.core.minify_html import minify_html
from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_fullpage_html_body,
    has_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_pdf_resource,
    is_url_resource,
)
from kash.kits.docs.actions.text.markdownify_doc import markdownify_doc
from kash.model import (
    ONE_ARG,
    TWO_ARGS,
    ActionInput,
    ActionResult,
    Format,
    ItemType,
    Param,
)
from prettyfmt import fmt_lines

from textpress.actions.textpress_render_template import textpress_render_template

log = get_logger(__name__)


@kash_action(
    expected_args=ONE_ARG,
    expected_outputs=TWO_ARGS,
    precondition=(
        is_url_resource | is_docx_resource | is_pdf_resource | has_html_body | has_simple_text_body
    )
    & ~has_fullpage_html_body,
    params=(
        Param("add_title", "Add a title to the page body.", type=bool),
        Param("add_classes", "Space-delimited classes to add to the body of the page.", type=str),
        Param("no_minify", "Skip HTML/CSS/JS/Tailwind minification step.", type=bool),
        Param(
            name="pdf_converter",
            description="The converter to use to convert the PDF to Markdown.",
            type=str,
            default_value="marker",
            valid_str_values=["markitdown", "marker"],
        ),
    ),
)
def textpress_format(
    input: ActionInput,
    add_title: bool = False,
    add_classes: str | None = None,
    no_minify: bool = False,
    pdf_converter: str = "marker",
) -> ActionResult:
    md_item = markdownify_doc(input, pdf_converter=pdf_converter).items[0]

    # Export the text item with original title or the heading if we can get it from the body.
    title = md_item.title or md_item.body_heading()
    md_item = md_item.derived_copy(type=ItemType.export, title=title)

    raw_html_item = textpress_render_template(md_item, add_title=add_title, add_classes=add_classes)

    if no_minify:
        html_body = raw_html_item.body
    else:
        minified_item = minify_html(raw_html_item)
        html_body = minified_item.body

    # Put the final formatted result as an export with the same title as the original.
    html_item = raw_html_item.derived_copy(
        type=ItemType.export,
        format=Format.html,
        title=title,
        body=html_body,
    )

    log.message("Formatted HTML item from text item:\n%s", fmt_lines([md_item, html_item]))
    if is_pdf_resource(input.items[0]):
        log.warning(
            "Converting from PDF to Markdown is not as reliable as from HTML or .docx. Check the output to confirm its quality!"
        )

    # Setting overwrite means we'll always pick the same output paths and
    # both .html and .md filenames will match.
    return ActionResult(items=[md_item, html_item], overwrite=True)
