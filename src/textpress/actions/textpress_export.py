from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_url_resource,
)
from kash.kits.docs.actions.text.create_docx import create_docx
from kash.kits.docs.actions.text.create_pdf import create_pdf
from kash.kits.docs.actions.text.markdownify_doc import markdownify_doc
from kash.model import (
    ActionInput,
    ActionResult,
)

log = get_logger(__name__)


@kash_action(precondition=is_url_resource | is_docx_resource | has_html_body | has_simple_text_body)
def textpress_export(input: ActionInput) -> ActionResult:
    md_item = markdownify_doc(input).items[0]

    docx_item = create_docx(md_item)
    pdf_item = create_pdf(md_item)

    return ActionResult(items=[docx_item, pdf_item])
