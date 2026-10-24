import pytest

from src.io.formats import (
    ApiKeyEntry,
    AppConfig,
    CustomProviderConfig,
    ProjectConfig,
    ProviderKeys,
)
from src.core.provider import (
    AnthropicProvider,
    CommandCodeProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    create_provider,
)


def _app_with_custom(api_type: str = "openai", base_url: str = "http://x/v1") -> AppConfig:
    return AppConfig(
        custom_providers=[
            CustomProviderConfig(
                name="local",
                label="Local server",
                api_type=api_type,
                base_url=base_url,
                models=["my-model"],
            )
        ],
        providers={"local": ProviderKeys(keys=[ApiKeyEntry(name="k", key="abc")])},
    )


class TestCustomProviderConfig:
    def test_appconfig_roundtrip(self):
        cfg = _app_with_custom()
        data = cfg.to_dict()

        assert data["custom_providers"][0]["name"] == "local"
        restored = AppConfig.from_dict(data)
        cp = restored.get_custom_provider("local")

        assert cp is not None
        assert cp.api_type == "openai"
        assert cp.base_url == "http://x/v1"
        assert cp.models == ["my-model"]
        assert restored.get_active_keys("local") == ["abc"]

    def test_missing_custom_providers_key_is_tolerated(self):
        restored = AppConfig.from_dict({"providers": {}})
        assert restored.custom_providers == []

    def test_display_name_falls_back_to_name(self):
        cp = CustomProviderConfig(name="abc")
        assert cp.display_name == "abc"
        cp.label = "Visible"
        assert cp.display_name == "Visible"


class TestProjectProviderField:
    def test_custom_provider_id_roundtrip(self):
        cfg = ProjectConfig(provider="mi_servidor")
        restored = ProjectConfig.from_dict(cfg.to_dict())
        assert restored.provider == "mi_servidor"

    def test_default_provider(self):
        assert ProjectConfig().provider == "gemini"


class TestCustomProviderFactory:
    def test_openai_compatible(self):
        provider = create_provider(_app_with_custom(), ProjectConfig(provider="local"))
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.name == "local"

    def test_anthropic(self):
        app = _app_with_custom(api_type="anthropic", base_url="https://api.anthropic.com")
        provider = create_provider(app, ProjectConfig(provider="local"))
        assert isinstance(provider, AnthropicProvider)
        assert provider.name == "local"

    def test_missing_base_url_raises(self):
        app = _app_with_custom(base_url="")
        with pytest.raises(ValueError):
            create_provider(app, ProjectConfig(provider="local"))

    def test_builtin_still_resolves(self):
        app = AppConfig(
            providers={"gemini": ProviderKeys(keys=[ApiKeyEntry(key="abc")])},
        )
        provider = create_provider(app, ProjectConfig(provider="gemini"))
        assert isinstance(provider, GeminiProvider)

    def test_commandcode_resolves(self):
        app = AppConfig(
            providers={"commandcode": ProviderKeys(keys=[ApiKeyEntry(key="abc")])},
        )
        provider = create_provider(app, ProjectConfig(provider="commandcode"))
        assert isinstance(provider, CommandCodeProvider)
        assert provider.name == "commandcode"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            create_provider(AppConfig(), ProjectConfig(provider="nope"))
