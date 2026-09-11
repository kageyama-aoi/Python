"""SettingsEditor.save_config の特性テスト（現行挙動の固定）。

第3弾リファクタ（#176）で save_config を分割する前に、
現在の入出力挙動を固定しておくためのテスト。
"""

import copy
import json
import os
import sys
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings_editor import SettingsEditor, parse_resizable
from src import constants as C

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
INITIAL_CONFIG_PATH = os.path.join(TEST_DATA_DIR, 'test_config_initial.json')


class TestSaveConfigCharacterization(unittest.TestCase):
    """save_config が ConfigManager へ渡す config の形を固定する。"""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        with open(INITIAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.saved = {}

        def _capture(cfg):
            self.saved['config'] = copy.deepcopy(cfg)
            return True

        self.cm = MagicMock()
        self.cm.get_config.return_value = self.config
        self.cm.save_config.side_effect = _capture

        self.callback = MagicMock()
        self.editor = SettingsEditor(self.root, self.cm, on_save_callback=self.callback)
        self.editor.update_idletasks()

    def tearDown(self):
        if self.editor.winfo_exists():
            self.editor.destroy()
        if self.root.winfo_exists():
            self.root.destroy()

    def _save(self):
        """messagebox を止めた状態で save_config を呼び、mock を返す。"""
        with patch('src.settings_editor.messagebox') as mb:
            self.editor.save_config()
        return mb

    # --- settings: resizable -------------------------------------------------

    def test_resizable_parsed_to_bool_list(self):
        self.editor.settings_vars[C.ConfigKey.RESIZABLE].set("True, False")
        self._save()
        self.assertEqual(self.saved['config']['settings']['resizable'], [True, False])

    def test_resizable_accepts_yes_and_digits(self):
        self.editor.settings_vars[C.ConfigKey.RESIZABLE].set("yes, 0, 1")
        self._save()
        self.assertEqual(self.saved['config']['settings']['resizable'], [True, False, True])

    # --- settings: menu_order ---------------------------------------------------

    def test_menu_order_display_name_normalized_to_value(self):
        self.editor.settings_vars[C.ConfigKey.MENU_ORDER].set("逆順")
        self._save()
        self.assertEqual(self.saved['config']['settings']['menu_order'], "reverse")

    def test_menu_order_global_rejected_at_top_level(self):
        self.editor.settings_vars[C.ConfigKey.MENU_ORDER].set("全体設定に従う")
        mb = self._save()
        mb.showerror.assert_called_once()
        self.cm.save_config.assert_not_called()

    # --- settings: initial_page ----------------------------------------------

    def test_initial_page_display_name_normalized_to_id(self):
        disp = self.editor.page_id_to_display['sub_menu']
        self.editor.settings_vars[C.ConfigKey.INITIAL_PAGE].set(disp)
        self._save()
        self.assertEqual(self.saved['config']['settings']['initial_page'], 'sub_menu')

    def test_initial_page_invalid_rejected(self):
        self.editor.settings_vars[C.ConfigKey.INITIAL_PAGE].set("存在しないページ")
        mb = self._save()
        mb.showerror.assert_called_once()
        self.cm.save_config.assert_not_called()

    # --- pages: 順序保持 ----------------------------------------------------

    def test_all_pages_preserved_after_save(self):
        before = set(self.editor.config['pages'].keys())
        self._save()
        self.assertEqual(set(self.saved['config']['pages'].keys()), before)

    # --- pages: per-page menu_order ----------------------------------------

    def test_page_menu_order_global_removes_key(self):
        page = next(iter(self.editor.page_menu_order_vars))
        self.editor.config['pages'][page]['menu_order'] = 'reverse'
        self.editor.page_menu_order_vars[page].set("全体設定に従う")
        self._save()
        self.assertNotIn('menu_order', self.saved['config']['pages'][page])

    def test_page_menu_order_value_stored(self):
        page = next(iter(self.editor.page_menu_order_vars))
        self.editor.page_menu_order_vars[page].set("逆順")
        self._save()
        self.assertEqual(self.saved['config']['pages'][page]['menu_order'], "reverse")

    # --- 保存成功時の副作用 -----------------------------------------------

    def test_successful_save_triggers_callback_and_destroy(self):
        self._save()
        self.callback.assert_called_once()
        self.assertFalse(self.editor.winfo_exists())


class TestParseResizable(unittest.TestCase):
    """save_config から切り出した純関数 parse_resizable の単体テスト。"""

    def test_true_false(self):
        self.assertEqual(parse_resizable("True, False"), [True, False])

    def test_various_true_tokens(self):
        self.assertEqual(parse_resizable("yes, 1, t, y"), [True, True, True, True])

    def test_case_and_whitespace_insensitive(self):
        self.assertEqual(parse_resizable("  TRUE ,  false "), [True, False])

    def test_non_true_tokens_are_false(self):
        self.assertEqual(parse_resizable("no, 0, off, "), [False, False, False, False])

    def test_empty_string_yields_single_false(self):
        self.assertEqual(parse_resizable(""), [False])


if __name__ == '__main__':
    unittest.main()
