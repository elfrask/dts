import pytest

from src.config.defaults import estimate_cost
from src.io.formats import AuditEntry, ProjectConfig


class TestEstimateCost:
    def test_known_model(self):
        cost = estimate_cost("deepseek/deepseek-v4.1-flash", 1_000_000, 1_000_000)
        assert cost == pytest.approx(0.75)

    def test_input_only(self):
        cost = estimate_cost("deepseek/deepseek-v4.1-flash", 1_000_000, 0)
        assert cost == pytest.approx(0.15)

    def test_unknown_model_is_free(self):
        assert estimate_cost("modelo/inexistente", 123456, 654321) == 0.0

    def test_zero_tokens(self):
        assert estimate_cost("gpt-4o", 0, 0) == 0.0


class TestAuditEntry:
    def test_total_tokens(self):
        entry = AuditEntry(input_tokens=120, output_tokens=30)
        assert entry.total_tokens == 150

    def test_roundtrip(self):
        entry = AuditEntry(
            timestamp="2026-07-23T12:00:00",
            provider="commandcode",
            model="deepseek/deepseek-v4.1-flash",
            input_tokens=1000,
            output_tokens=250,
            dialogs=20,
            attempts=2,
            cost=0.0003,
        )
        restored = AuditEntry.from_dict(entry.to_dict())
        assert restored == entry

    def test_from_dict_tolerates_missing_fields(self):
        entry = AuditEntry.from_dict({})
        assert entry.input_tokens == 0
        assert entry.output_tokens == 0
        assert entry.attempts == 1
        assert entry.cost == 0.0


class TestAuditProjectConfig:
    def test_roundtrip(self):
        cfg = ProjectConfig(
            route_audit_file="logs/audit.json",
            paused_mode=False,
        )
        restored = ProjectConfig.from_dict(cfg.to_dict())
        assert restored.route_audit_file == "logs/audit.json"
        assert restored.paused_mode is False

    def test_defaults(self):
        cfg = ProjectConfig()
        assert cfg.route_audit_file == "audit.json"
        assert cfg.paused_mode is True
