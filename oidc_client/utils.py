"""General utilities."""

from typing import Any


def join_url(base: str, *path: str) -> str:
    """Join URLs using the common "/" separator.

    :param base: base url.
    :param `*path`: paths to join.
    :return: concatenated URL without last "/".
    """
    return "/".join(str(s).rstrip("/") for s in [base, *path])


def add_query_params(base: str, *params: tuple[str, Any], first_delimiter: str = "&"):
    return base + first_delimiter + "&".join(f"{k}={v}" for k, v in params)
