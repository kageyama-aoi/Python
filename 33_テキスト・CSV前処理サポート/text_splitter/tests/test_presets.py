"""
presets.py（名前付きプリセット）のユニットテスト。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from presets import get_preset_options, load_presets, save_presets
from run import SplitOptions


class TestPresets(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "presets.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_load_missing_file_returns_empty(self):
        """ファイルがなければ空 dict（エラーにしない）"""
        self.assertEqual(load_presets(self.path), {})

    def test_save_and_load_roundtrip(self):
        presets = {
            "テスト用": {"rows_per_file": 100, "encoding": "utf-8", "has_header": True, "delimiter": None},
            "タブ区切り": {"rows_per_file": 500, "encoding": "shift_jis", "has_header": False, "delimiter": "\t"},
        }
        save_presets(presets, self.path)
        loaded = load_presets(self.path)
        self.assertEqual(loaded, presets)
        self.assertEqual(list(loaded), ["テスト用", "タブ区切り"])  # 順序保持

    def test_get_preset_options(self):
        save_presets(
            {"銀行用": {"rows_per_file": 45000, "encoding": "utf-8", "has_header": False, "delimiter": None}},
            self.path,
        )
        opts = get_preset_options("銀行用", self.path)
        self.assertIsInstance(opts, SplitOptions)
        self.assertEqual(opts.rows_per_file, 45000)
        self.assertFalse(opts.has_header)
        self.assertIsNone(opts.delimiter)

    def test_get_preset_options_defaults(self):
        """has_header 省略時は True、delimiter 省略・空文字は None"""
        save_presets({"最小": {"rows_per_file": 10, "encoding": "utf-8"}}, self.path)
        opts = get_preset_options("最小", self.path)
        self.assertTrue(opts.has_header)
        self.assertIsNone(opts.delimiter)

        save_presets({"空delim": {"rows_per_file": 10, "encoding": "utf-8", "delimiter": ""}}, self.path)
        self.assertIsNone(get_preset_options("空delim", self.path).delimiter)

    def test_unknown_name_raises_keyerror_with_available(self):
        save_presets({"登録済み": {"rows_per_file": 10, "encoding": "utf-8"}}, self.path)
        with self.assertRaises(KeyError) as ctx:
            get_preset_options("存在しない", self.path)
        self.assertIn("存在しない", ctx.exception.args[0])
        self.assertIn("登録済み", ctx.exception.args[0])

    def test_invalid_structure_raises(self):
        """dict-of-dict でないJSONは ValueError"""
        self.path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_presets(self.path)
        self.path.write_text(json.dumps({"名前": "設定がdictでない"}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_presets(self.path)

    def test_example_template_is_loadable(self):
        """同梱の presets.example.json が正しい形式である"""
        example = Path(__file__).parent.parent / "config" / "presets.example.json"
        presets = load_presets(example)
        self.assertGreater(len(presets), 0)
        for name in presets:
            opts = get_preset_options(name, example)
            opts.validate()


if __name__ == "__main__":
    unittest.main()
