"""Tiny stdlib JSON HTTP client.

DTS talks to OpenAI-compatible and Anthropic endpoints directly over HTTPS.
Using ``urllib`` removes the dependency on the generated ``openai`` SDK, which
is large and can be left in a broken state by interrupted installs.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 180


def _decode_body(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def _raise_http_error(exc: urllib.error.HTTPError) -> None:
    try:
        detail = _decode_body(exc.read())[:600]
    except Exception:
        detail = ""
    raise RuntimeError(f"HTTP {exc.code}: {detail or exc.reason}") from exc


def _request(
    url: str,
    *,
    method: str,
    api_key: str,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "dts/2.2.1")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    for k, v in (headers or {}).items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = _decode_body(resp.read())
    except urllib.error.HTTPError as exc:
        _raise_http_error(exc)
        raise  # unreachable, keeps type checkers happy
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error: {exc.reason}") from exc

    if not body.strip():
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from {url}: {body[:300]}") from exc


def post_json(
    url: str,
    payload: dict,
    api_key: str = "",
    *,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    return _request(
        url, method="POST", api_key=api_key, payload=payload,
        headers=headers, timeout=timeout,
    )


def get_json(
    url: str,
    api_key: str = "",
    *,
    headers: Optional[dict] = None,
    timeout: int = 60,
) -> dict:
    return _request(
        url, method="GET", api_key=api_key, payload=None,
        headers=headers, timeout=timeout,
    )


def join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"
