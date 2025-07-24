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
    # Build social metadata from item fields
    social_meta = {}
    if item.title:
        social_meta["title"] = item.title
    if item.description:
        social_meta["description"] = item.description
    if item.thumbnail_url:
        social_meta["image"] = item.thumbnail_url
    if item.url:
        social_meta["url"] = item.url

    # Check for additional social metadata in extra fields
    if item.extra:
        if "social_type" in item.extra:
            social_meta["type"] = item.extra["social_type"]
        if "site_name" in item.extra:
            social_meta["site_name"] = item.extra["site_name"]
        if "twitter_handle" in item.extra:
            social_meta["twitter_handle"] = item.extra["twitter_handle"]

    with additional_template_dirs(templates_dir):
        return render_web_template(
            "textpress_webpage.html.jinja",
            data={
                "title": item.title,
                "add_title_h1": add_title_h1,
                "add_classes": add_classes,
                "content_html": item.body_as_html(),
                "thumbnail_url": item.thumbnail_url,
                "social_meta": social_meta if social_meta else None,
                "enable_themes": True,
                "show_theme_toggle": False,
            },
        )
