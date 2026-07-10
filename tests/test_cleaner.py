from src.processors.cleaner import clean_values, clean_codes, clean_void


class TestCleanValues:
    def test_removes_traduccion_prefix(self):
        data = {"traduccion_foo": "bar"}
        result = clean_values(data)
        assert "foo" in result

    def test_removes_Traduccion_prefix(self):
        data = {"Traducción_foo": "bar"}
        result = clean_values(data)
        assert "foo" in result

    def test_leaves_clean_keys(self):
        data = {"normal_key": "value"}
        result = clean_values(data)
        assert result == {"normal_key": "value"}


class TestCleanCodes:
    def test_removes_special_chars(self):
        result = clean_codes("hello!@#world")
        assert result == "helloworld"

    def test_preserves_alphanumeric(self):
        result = clean_codes("hello world 123")
        assert result == "hello world 123"

    def test_preserves_underscore(self):
        result = clean_codes("hello_world")
        assert result == "hello_world"


class TestCleanVoid:
    def test_removes_empty_translations(self):
        data = {"key1": "", "key2": "hello"}
        original = {"key1": "original1", "key2": "original2"}
        result = clean_void(data, original)
        assert "key1" not in result
        assert "key2" in result

    def test_keeps_empty_if_original_also_empty(self):
        data = {"key1": ""}
        original = {"key1": ""}
        result = clean_void(data, original)
        assert "key1" in result
