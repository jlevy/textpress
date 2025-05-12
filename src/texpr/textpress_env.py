from clideps.env_vars.env_enum import EnvEnum


class Env(EnvEnum):
    """
    Environment variable settings for Textpress.
    """

    TEXTPRESS_API_ROOT = "TEXTPRESS_API_ROOT"
    """The root directory for Textpress API."""

    TEXTPRESS_API_KEY = "TEXTPRESS_API_KEY"
    """The API key for Textpress."""

    # TODO: These should probably be gotten from the API.
    TEXTPRESS_PUBLISH_ROOT = "TEXTPRESS_PUBLISH_ROOT"
    """The root directory for Textpress publish."""

    TEXTPRESS_USERNAME = "TEXTPRESS_USERNAME"
    """The username for Textpress."""
