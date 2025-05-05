import logging
from pathlib import Path

import httpx

log = logging.getLogger(__name__)


def publish(paths: list[Path]) -> None:
    """
    Publishes a list of files to Textpress.
    """
    from texpr.textpress_api import publish_files

    try:
        manifest = publish_files(paths)
        files = manifest.files.keys()
        log.warning("Published %d files: %s", len(files), ", ".join(files))
    except (httpx.HTTPStatusError, ValueError, FileNotFoundError) as e:
        # Catch specific, expected errors.
        log.exception("Publishing failed: %s", e)
    except Exception as e:
        log.exception("An unexpected error occurred during publishing: %s", e)
