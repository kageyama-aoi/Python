"""設定エディタのボタン設定フォーム（未保存ガード・アクション切替）のテスト。"""

import json
import os
import sys
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings_editor import SettingsEditor
from src import constants as C

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
INITIAL_CONFIG_PATH = os.path.join(TEST_DATA_DIR, 'test_config_initial.json')


class TestButtonForm(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        with open(INITIAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        cm = MagicMock()
        cm.get_config.return_value = self.config
        self.editor = SettingsEditor(self.root, cm)
        self.editor.update_idletasks()
        self.pages = list(self.editor.config['pages'].keys())

    def tearDown(self):
        if self.editor.winfo_exists():
            self.editor.destroy()
        if self.root.winfo_exists():
            self.root.destroy()

    def _F(self, key):
        return self.editor.form_entries[key]

    def test_switching_action_clears_carried_over_value(self):
        """アクションを切り替えると前アクション用の入力値が残らない（#158）。"""
        self.editor.add_button(self.pages[0])
        self._F(C.ConfigKey.NAME).set("マイリンク")
        self._F(C.ConfigKey.ACTION).set(C.Action.OPEN_URL.value)
        self._F(C.ConfigKey.PATH).set("https://example.com")

        # ユーザー操作としてアクションを切り替え
        self._F(C.ConfigKey.ACTION).set(C.Action.OPEN_DIRECTORY.value)
        self.editor._on_action_selected()

        self.assertEqual(self._F(C.ConfigKey.PATH).get(), "", "パス欄に前の値が残っています。")
        self.assertEqual(self._F(C.ConfigKey.NAME).get(), "マイリンク", "名前まで消えています。")

    def test_dirty_flag_and_discard_guard(self):
        """未保存の入力があると add_button が確認を挟む（#158）。"""
        self.editor.add_button(self.pages[0])
        self.assertFalse(self.editor.form_has_unsaved_changes())

        self._F(C.ConfigKey.NAME).set("下書き")
        self.assertTrue(self.editor.form_has_unsaved_changes())

        with patch("src.button_form.messagebox.askyesno", return_value=False) as m:
            self.editor.add_button(self.pages[0])
            m.assert_called_once()
        # 破棄しなかったので下書きは残る
        self.assertEqual(self._F(C.ConfigKey.NAME).get(), "下書き")

        with patch("src.button_form.messagebox.askyesno", return_value=True):
            self.editor.add_button(self.pages[0])
        self.assertEqual(self._F(C.ConfigKey.NAME).get(), "")

    def test_save_targets_form_page_not_current_tab(self):
        """保存はフォームを開いたページへ行う（表示タブに依存しない）（#158）。"""
        page_a, page_b = self.pages[0], self.pages[1]
        len_b_before = len(self.editor.config['pages'][page_b]['entries'])

        self.editor.add_button(page_a)  # フォームは page_a に紐づく
        self._F(C.ConfigKey.NAME).set("Aに追加")
        self._F(C.ConfigKey.ACTION).set(C.Action.OPEN_URL.value)
        self._F(C.ConfigKey.PATH).set("https://a.example")

        # 表示タブを page_b へ切り替えてから保存
        nb = self.editor.pages_widgets["pages_notebook"]
        nb.select(self.editor.page_name_to_frame[page_b])
        self.editor.save_form_data()

        names_a = [e.get("name") for e in self.editor.config['pages'][page_a]['entries']]
        self.assertIn("Aに追加", names_a, "page_a へ保存されていません。")
        self.assertEqual(
            len(self.editor.config['pages'][page_b]['entries']), len_b_before,
            "表示中だった page_b に誤って追加されています。",
        )


if __name__ == '__main__':
    unittest.main()
