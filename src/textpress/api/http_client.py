import atexit
from typing import Any

import httpx
from strif import AtomicVar

default_client_settings: dict[str, Any] = {
    # httpx's default timeout of 5 seconds is pretty short.
    "timeout": 120,
}

_http_client: AtomicVar[httpx.Client | None] = AtomicVar(None)


def get_http_client() -> httpx.Client:
    """
    Simple global, lazily initialized `httpx.Client` with default settings.
    Can be shared across threads.
    """
    with _http_client.lock:
        client = _http_client.value
        if client is None or client.is_closed:
            client = httpx.Client(**default_client_settings)
            _http_client.set(client)
        return client


def close_http_client() -> None:
    """
    Idempotent close of global `httpx.Client`.
    """
    with _http_client.lock:
        client = _http_client.value
        if client is not None and not client.is_closed:
            client.close()
            _http_client.set(None)


atexit.register(close_http_client)
