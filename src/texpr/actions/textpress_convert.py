from kash.exec import kash_action
from kash.exec.preconditions import is_docx_resource
from kash.kits.docs.actions.text.docx_to_md import docx_to_md
from kash.kits.docs.actions.text.endnotes_to_footnotes import endnotes_to_footnotes
from kash.model import Item


@kash_action(precondition=is_docx_resource)
def textpress_convert(item: Item) -> Item:
    # First do basic conversion to markdown.
    md_item = docx_to_md(item)

    # Gemini reports use superscripts with a long list of numeric references.
    # This converts them to proper footnotes.
    footnotes_item = endnotes_to_footnotes(md_item)

    return footnotes_item
