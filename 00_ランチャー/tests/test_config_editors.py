"""config_editors の純ロジック（tkinter 非依存）の回帰テスト。

対象は「壊れるとユーザーの設定ファイルを破損させる」3関数:
- describe_json_value / coerce_json_value : config.json の型ラウンドトリップ
- replace_ini_value_line                 : config.ini のコメント保持行置換
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config_editors import (  # noqa: E402
    coerce_json_value,
    describe_json_value,
    replace_ini_value_line,
)


class TestDescribeJsonValue(unittest.TestCase):
    def test_bool_before_int(self):
        self.assertEqual(describe_json_value(True), ("bool", True))
        self.assertEqual(describe_json_value(False), ("bool", False))

    def test_str(self):
        self.assertEqual(describe_json_value("abc"), ("str", "abc"))

    def test_int_and_float_become_text(self):
        self.assertEqual(describe_json_value(42), ("number", "42"))
        self.assertEqual(describe_json_value(1.5), ("number", "1.5"))

    def test_list_of_str_is_comma_joined(self):
        self.assertEqual(describe_json_value(["a", "b"]), ("list_str", "a, b"))

    def test_list_with_non_str_falls_back_to_json(self):
        kind, text = describe_json_value(["a", 1])
        self.assertEqual(kind, "json")
        self.assertEqual(json.loads(text), ["a", 1])

    def test_dict_is_json(self):
        kind, text = describe_json_value({"k": "v"})
        self.assertEqual(kind, "json")
        self.assertEqual(json.loads(text), {"k": "v"})

    def test_json_text_keeps_non_ascii(self):
        _, text = describe_json_value({"名前": "太郎"})
        self.assertIn("名前", text)
        self.assertIn("太郎", text)


class TestCoerceJsonValue(unittest.TestCase):
    def test_bool(self):
        self.assertIs(coerce_json_value("bool", True, False), True)

    def test_number_preserves_int_type(self):
        result = coerce_json_value("number", "10", 0)
        self.assertEqual(result, 10)
        self.assertIsInstance(result, int)

    def test_number_preserves_float_type(self):
        result = coerce_json_value("number", "2.5", 0.0)
        self.assertIsInstance(result, float)

    def test_number_invalid_raises_value_error(self):
        with self.assertRaises(ValueError):
            coerce_json_value("number", "abc", 0)

    def test_list_str_splits_trims_and_drops_empty(self):
        self.assertEqual(coerce_json_value("list_str", "a, b ,, c ,", []), ["a", "b", "c"])

    def test_json_parses(self):
        self.assertEqual(coerce_json_value("json", '{"k": 1}', {}), {"k": 1})

    def test_json_invalid_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            coerce_json_value("json", "{bad}", {})

    def test_str_passthrough_keeps_surrounding_spaces(self):
        self.assertEqual(coerce_json_value("str", "  keep ", ""), "  keep ")

    def test_describe_then_coerce_roundtrips(self):
        for original in [True, False, 3, 4.5, "x", ["a", "b"], {"k": "v"}]:
            kind, text = describe_json_value(original)
            self.assertEqual(coerce_json_value(kind, text, original), original)


class TestReplaceIniValueLine(unittest.TestCase):
    @staticmethod
    def _lines(text):
        return text.splitlines(keepends=True)

    def test_replaces_only_target_key(self):
        lines = self._lines("[A]\nx = 1\ny = 2\n")
        self.assertTrue(replace_ini_value_line(lines, "A", "x", "9"))
        self.assertEqual("".join(lines), "[A]\nx = 9\ny = 2\n")

    def test_keeps_comments_and_blank_lines(self):
        src = "; 見出しコメント\n[A]\n# メモ\nkey = old\n\n[B]\nkey = keep\n"
        lines = self._lines(src)
        self.assertTrue(replace_ini_value_line(lines, "A", "key", "new"))
        self.assertEqual(
            "".join(lines),
            "; 見出しコメント\n[A]\n# メモ\nkey = new\n\n[B]\nkey = keep\n",
        )

    def test_same_key_in_other_section_untouched(self):
        lines = self._lines("[A]\nkey = a\n[B]\nkey = b\n")
        self.assertTrue(replace_ini_value_line(lines, "B", "key", "B2"))
        self.assertEqual("".join(lines), "[A]\nkey = a\n[B]\nkey = B2\n")

    def test_preserves_indentation_and_colon_separator(self):
        lines = self._lines("[A]\n  key : old\n")
        self.assertTrue(replace_ini_value_line(lines, "A", "key", "new"))
        self.assertEqual("".join(lines), "[A]\n  key : new\n")

    def test_missing_key_returns_false(self):
        lines = self._lines("[A]\nx = 1\n")
        self.assertFalse(replace_ini_value_line(lines, "A", "missing", "v"))

    def test_missing_section_returns_false(self):
        lines = self._lines("[A]\nx = 1\n")
        self.assertFalse(replace_ini_value_line(lines, "Z", "x", "v"))

    def test_last_line_without_trailing_newline(self):
        lines = self._lines("[A]\nx = 1")
        self.assertTrue(replace_ini_value_line(lines, "A", "x", "2"))
        self.assertEqual("".join(lines), "[A]\nx = 2")

    def test_commented_out_key_is_skipped(self):
        lines = self._lines("[A]\n# key = commented\nkey = real\n")
        self.assertTrue(replace_ini_value_line(lines, "A", "key", "new"))
        self.assertEqual("".join(lines), "[A]\n# key = commented\nkey = new\n")


if __name__ == "__main__":
    unittest.main()
