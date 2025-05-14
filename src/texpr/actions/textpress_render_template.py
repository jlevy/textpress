from kash.exec import kash_action
from kash.exec.preconditions import (
    has_full_html_page_body,
    has_simple_text_body,
    is_html,
)
from kash.model import ONE_OR_MORE_ARGS, Format, Item, Param

from texpr.render_webpage import render_webpage


@kash_action(
    expected_args=ONE_OR_MORE_ARGS,
    precondition=(is_html | has_simple_text_body) & ~has_full_html_page_body,
    params=(Param("add_title", "Add a title to the page body.", type=bool),),
)
def textpress_render_template(item: Item, add_title: bool = False) -> Item:
    html_body = render_webpage(item, add_title_h1=add_title)
    html_item = item.derived_copy(format=Format.html, body=html_body)

    return html_item
