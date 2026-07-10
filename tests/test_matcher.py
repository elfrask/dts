from src.io.formats import StringsFile, TranslationDict
from src.processors.matcher import (
    generate_input,
    check_commands,
    apply_strings,
    merge_dicts,
    manual_generate,
    manual_apply,
)


SAMPLE_STRINGS = StringsFile(Strings=[
    "gml_Script_scr_something",
    "ignore_me",
    "obj_slash_room_gml_1_0",
    "Hello, world!",
    "obj_slash_room_gml_2_0",
    "Another dialog",
    "obj_slash_room_gml_3_0",
    "internal_var",
    "obj_slash_room_gml_4_0",
    "With \\command*",
])


class TestGenerateInput:
    def test_generates_key_dialog_pairs(self):
        result = generate_input(SAMPLE_STRINGS)
        assert "obj_slash_room_gml_1_0" in result.data
        assert result.data["obj_slash_room_gml_1_0"] == "Hello, world!"
        assert "obj_slash_room_gml_2_0" in result.data
        assert result.data["obj_slash_room_gml_2_0"] == "Another dialog"

    def test_skips_gml_script(self):
        result = generate_input(SAMPLE_STRINGS)
        assert "gml_Script_scr_something" not in result.data

    def test_skips_lowercase_no_spaces(self):
        result = generate_input(SAMPLE_STRINGS)
        assert "obj_slash_room_gml_3_0" not in result.data
        assert "internal_var" not in result.data


class TestCheckCommands:
    def test_adds_prefix_if_missing(self):
        result = check_commands("hello", "\\command")
        assert result == "\\hello"

    def test_adds_suffix_if_missing(self):
        result = check_commands("hello", "/%")
        assert result == "hello/%"

    def test_preserves_existing_prefix(self):
        result = check_commands("\\hello", "\\world")
        assert result == "\\hello"

    def test_preserves_existing_suffix(self):
        result = check_commands("hello/%", "world/%")
        assert result == "hello/%"


class TestApplyStrings:
    def test_replaces_dialogs(self):
        strings = StringsFile(Strings=[
            "obj_slash_room_gml_1_0",
            "Original dialog",
        ])
        translations = TranslationDict(data={
            "obj_slash_room_gml_1_0": "Translated dialog",
        })
        result = apply_strings(strings, translations)
        assert result.Strings[1] == "Translated dialog"

    def test_preserves_unchanged_keys(self):
        strings = StringsFile(Strings=["unchanged", "dialog"])
        translations = TranslationDict(data={})
        result = apply_strings(strings, translations)
        assert result.Strings == ["unchanged", "dialog"]


class TestMergeDicts:
    def test_overlay_overrides_original(self):
        result = merge_dicts({"a": "1", "b": "2"}, {"b": "3", "c": "4"})
        assert result == {"a": "1", "b": "3", "c": "4"}


class TestManualGenerate:
    def test_finds_missing_keys(self):
        original = TranslationDict(data={"a": "1", "b": "2", "c": "3"})
        translated = TranslationDict(data={"a": "1"})
        result = manual_generate(original, translated)
        assert result.data == {"b": "2", "c": "3"}


class TestManualApply:
    def test_merges_manual_over_current(self):
        current = TranslationDict(data={"a": "1", "b": "2"})
        manual = TranslationDict(data={"b": "edited", "c": "new"})
        result = manual_apply(current, manual)
        assert result.data == {"a": "1", "b": "edited", "c": "new"}
