from kash.exec import kash_action
from kash.exec.preconditions import (
    has_fullpage_html_body,
    has_html_body,
    has_simple_text_body,
)
from kash.model import ONE_OR_MORE_ARGS, Format, Item, Param

from textpress.docs.render_webpage import render_webpage


@kash_action(
    expected_args=ONE_OR_MORE_ARGS,
    precondition=(has_html_body | has_simple_text_body) & ~has_fullpage_html_body,
    params=(
        Param("add_title", "Add a title to the page body.", type=bool),
        Param("add_classes", "Space-delimited classes to add to the body of the page.", type=str),
    ),
)
def textpress_render_template(
    item: Item, add_title: bool = False, add_classes: str | None = None
) -> Item:
    html_body = render_webpage(item, add_title_h1=add_title, add_classes=add_classes)
    html_item = item.derived_copy(format=Format.html, body=html_body)

    return html_item
