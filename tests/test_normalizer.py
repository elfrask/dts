import pytest
from src.processors.normalizer import (
    normalice_text,
    normalice_text_new,
    clean_normalice,
    clean_normalice_new,
)


class TestNormaliceText:
    def test_removes_accents(self):
        result = normalice_text("canción")
        assert result == "cancion"

    def test_strips_non_ascii_chars(self):
        result = normalice_text("\u201cHola\u201d")
        assert result == "Hola"

    def test_ascii_only(self):
        result = normalice_text("ñandú")
        assert result == "nandu"


class TestNormaliceTextNew:
    def test_secure_mode_removes_accents(self):
        result = normalice_text_new("canción", secure=True)
        assert result == "cancion"

    def test_secure_mode_removes_opening_marks(self):
        result = normalice_text_new("\u00a1Hola\u00bf", secure=True)
        assert result == "Hola"

    def test_non_secure_preserves_accents(self):
        result = normalice_text_new("canción", secure=False)
        assert "ó" in result

    def test_non_string_returns_unchanged(self):
        result = normalice_text_new(123, secure=False)
        assert result == 123

    def test_fixes_curly_quotes(self):
        result = normalice_text_new("\u201cHola\u201d", secure=False)
        assert result == '"Hola"'


class TestCleanNormalice:
    def test_normalizes_all_values(self):
        data = {"key1": "canción", "key2": "ñandú"}
        result = clean_normalice(data)
        assert result == {"key1": "cancion", "key2": "nandu"}


class TestCleanNormaliceNew:
    def test_secure_flag(self):
        data = {"key1": "canción"}
        result = clean_normalice_new(data, secure=True)
        assert result == {"key1": "cancion"}

    def test_non_secure_preserves_accents(self):
        data = {"key1": "canción"}
        result = clean_normalice_new(data, secure=False)
        assert result == {"key1": "canción"}
