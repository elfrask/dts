"""Dynamic model discovery for every supported API shape.

Each helper returns a list of model identifiers offered by the provider, or an
empty list when the provider cannot be reached. Callers are expected to fall
back to a statically known list when this happens.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

API_TYPE_OPENAI = "openai"
API_TYPE_ANTHROPIC = "anthropic"
API_TYPE_GEMINI = "gemini"
API_TYPE_OLLAMA = "ollama"
API_TYPE_COMMANDCODE = "commandcode"


def fetch_openai_models(base_url: str, api_key: str) -> list[str]:
    """List models from any OpenAI-compatible endpoint (GET /models)."""
    if not api_key or not base_url:
        return []
    try:
        from src.core.http_client import get_json, join_url

        data = get_json(join_url(base_url, "models"), api_key)
        names = [
            m.get("id") for m in data.get("data", [])
            if isinstance(m, dict) and m.get("id")
        ]
        return sorted(names)
    except Exception as e:
        logger.warning("Could not fetch models from %s: %s", base_url, e)
        return []


def fetch_anthropic_models(api_key: str, base_url: Optional[str] = None) -> list[str]:
    """List models from Anthropic (GET /v1/models)."""
    if not api_key:
        return []
    try:
        import anthropic

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = anthropic.Anthropic(**kwargs)
        resp = client.models.list()
        names = [m.id for m in resp.data if getattr(m, "id", None)]
        return sorted(names)
    except Exception as e:
        logger.warning("Could not fetch Anthropic models: %s", e)
        return []


def fetch_gemini_models(api_key: str) -> list[str]:
    """List Gemini models, stripping the ``models/`` prefix."""
    if not api_key:
        return []
    try:
        import google.genai as genai

        client = genai.Client(api_key=api_key)
        names = []
        for m in client.models.list():
            name = getattr(m, "name", "") or ""
            if name.startswith("models/"):
                name = name[len("models/"):]
            if not name or "embedding" in name:
                continue
            if not name.startswith("gemini"):
                continue
            names.append(name)
        return sorted(names)
    except Exception as e:
        logger.warning("Could not fetch Gemini models: %s", e)
        return []


def fetch_commandcode_models(api_key: str) -> list[str]:
    """List CommandCode chat models, excluding decision-only models."""
    from src.config.defaults import COMMANDCODE_BASE_URL

    names = fetch_openai_models(COMMANDCODE_BASE_URL, api_key)
    return [m for m in names if not m.startswith("typesafe/")]


def fetch_ollama_models(host: str, port: int) -> list[str]:
    """List locally installed Ollama models."""
    try:
        import ollama

        client = ollama.Client(host=f"{host}:{port}")
        resp = client.list()
        return [m.model for m in resp.models]  # type: ignore
    except Exception as e:
        logger.warning("Could not fetch Ollama models: %s", e)
        return []


def fetch_models(api_type: str, api_key: str, base_url: str = "") -> list[str]:
    """Dispatch to the correct fetcher based on ``api_type``."""
    if api_type == API_TYPE_ANTHROPIC:
        return fetch_anthropic_models(api_key, base_url or None)
    if api_type == API_TYPE_GEMINI:
        return fetch_gemini_models(api_key)
    if api_type == API_TYPE_COMMANDCODE:
        return fetch_commandcode_models(api_key)
    return fetch_openai_models(base_url, api_key)
