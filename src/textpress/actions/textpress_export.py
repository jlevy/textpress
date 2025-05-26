from kash.config.logger import get_logger
from kash.exec import kash_action
from kash.exec.preconditions import (
    has_html_body,
    has_simple_text_body,
    is_docx_resource,
    is_url_resource,
)
from kash.kits.docs.doc_formats.simple_html_to_docx import SimpleHtmlToDocx
from kash.model import (
    ONE_ARG,
    TWO_ARGS,
    ActionInput,
    ActionResult,
    Format,
    ItemType,
)
from kash.utils.file_utils.file_ext import FileExt
from kash.workspaces import current_ws
from strif import atomic_output_file

from textpress.actions.textpress_convert import textpress_convert

log = get_logger(__name__)


@kash_action(
    expected_args=ONE_ARG,
    expected_outputs=TWO_ARGS,
    precondition=(is_url_resource | is_docx_resource | has_html_body | has_simple_text_body),
)
def textpress_export(input: ActionInput) -> ActionResult:
    md_item = textpress_convert(input).items[0]

    docx_item = md_item.derived_copy(
        type=ItemType.export, format=Format.docx, file_ext=FileExt.docx
    )
    docx_path, _found, _old_docx_path = current_ws().store_path_for(docx_item)
    full_docx_path = current_ws().base_dir / docx_path

    content_html = md_item.body_as_html()
    docx = SimpleHtmlToDocx().convert_html_string(content_html)
    with atomic_output_file(full_docx_path, make_parents=True) as f:
        docx.save(str(f))

    docx_item.external_path = str(full_docx_path)

    return ActionResult(items=[docx_item])
