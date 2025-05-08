import os


def get_api_root() -> str:
    api_root = os.getenv("TEXTPRESS_API_ROOT")
    if not api_root:
        raise ValueError("TEXTPRESS_API_ROOT environment variable not set.")
    return api_root


def get_api_key() -> str:
    api_key = os.getenv("TEXTPRESS_API_KEY")
    if not api_key:
        raise ValueError("TEXTPRESS_API_KEY environment variable not set.")
    return api_key
