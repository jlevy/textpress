from pathlib import Path

from kash.model import Item
from kash.web_gen.template_render import additional_template_dirs, render_web_template

templates_dir = Path(__file__).parent / "templates"


def render_webpage(item: Item, add_title_h1: bool = False, add_classes: str | None = None) -> str:
    """
    Generate a simple web page from a single item.
    If `add_title_h1` is True, the title will be inserted as an h1 heading above the body.
    If `add_classes` is provided, they will be added to the body as a class attribute.
    """
    with additional_template_dirs(templates_dir):
        return render_web_template(
            "textpress_webpage.html.jinja",
            data={
                "title": item.title,
                "add_title_h1": add_title_h1,
                "add_classes": add_classes,
                "content_html": item.body_as_html(),
                "thumbnail_url": item.thumbnail_url,
                "enable_themes": True,
                "show_theme_toggle": False,
            },
        )
