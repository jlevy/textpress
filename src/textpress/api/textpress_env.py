from dataclasses import dataclass

from clideps.env_vars.env_enum import EnvEnum
from strif import abbrev_str
from typing_extensions import override


class Env(EnvEnum):
    """
    Environment variable settings for Textpress.
    """

    TEXTPRESS_API_ROOT = "TEXTPRESS_API_ROOT"
    """The root directory for Textpress API."""

    TEXTPRESS_API_KEY = "TEXTPRESS_API_KEY"
    """The API key for Textpress."""

    TEXTPRESS_PUBLISH_ROOT = "TEXTPRESS_PUBLISH_ROOT"
    """The root directory for Textpress publish."""


@dataclass(frozen=True)
class ApiConfig:
    """
    Configuration for the Textpress API.
    """

    api_key: str
    api_root: str
    publish_root: str

    @override
    def __str__(self) -> str:
        return f"api_key={abbrev_str(self.api_key, 10)}, api_root={self.api_root}, publish_root={self.publish_root}"


def get_api_config() -> ApiConfig:
    """
    Get the API config from the environment variables.
    """
    return ApiConfig(
        api_key=Env.TEXTPRESS_API_KEY.read_str(),
        api_root=Env.TEXTPRESS_API_ROOT.read_str(default="https://app.textpress.md"),
        publish_root=Env.TEXTPRESS_PUBLISH_ROOT.read_str(default="https://textpress.md"),
    )


LOGIN_URL = "https://app.textpress.md/login"
"""The URL for the Textpress login page."""
