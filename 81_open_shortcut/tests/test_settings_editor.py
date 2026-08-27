"""設定エディタ（SettingsEditor）のレイアウト・回帰テスト。"""

import json
import os
import sys
import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings_editor import SettingsEditor

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
INITIAL_CONFIG_PATH = os.path.join(TEST_DATA_DIR, 'test_config_initial.json')


class TestSettingsEditorLayout(unittest.TestCase):
    """設定エディタのウィジェット配置に関するテスト。"""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

        with open(INITIAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.mock_cm = MagicMock()
        self.mock_cm.get_config.return_value = self.config

        self.editor = SettingsEditor(self.root, self.mock_cm)
        self.editor.update_idletasks()

    def tearDown(self):
        if self.editor.winfo_exists():
            self.editor.destroy()
        if self.root.winfo_exists():
            self.root.destroy()

    def _find_button(self, parent, text):
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget("text") == text:
                return widget
            found = self._find_button(widget, text)
            if found:
                return found
        return None

    def test_save_button_is_bottom_anchored(self):
        """保存ボタンは Notebook より先に下端へ確保され、潰れないこと（#148）。"""
        save_button = self._find_button(self.editor, "保存して閉じる")
        self.assertIsNotNone(save_button, "「保存して閉じる」ボタンが見つかりません。")
        self.assertEqual(
            save_button.pack_info().get("side"), "bottom",
            "保存ボタンが下端（side=bottom）に配置されていません。",
        )

    def test_save_button_not_crushed_at_min_size(self):
        """最小サイズでも保存ボタンの高さが要求高さ分確保されること（#148）。"""
        self.editor.geometry("740x620")
        self.editor.update_idletasks()

        save_button = self._find_button(self.editor, "保存して閉じる")
        self.assertIsNotNone(save_button)

        req_h = save_button.winfo_reqheight()
        actual_h = save_button.winfo_height()
        self.assertGreaterEqual(
            actual_h, req_h - 1,
            f"保存ボタンが潰れています（要求 {req_h}px / 実際 {actual_h}px）。",
        )
        self.assertGreater(actual_h, 16, "保存ボタンの高さが小さすぎます。")

    def test_status_label_above_save_button(self):
        """ステータス表示も下端側に確保されていること。"""
        self.assertTrue(hasattr(self.editor, "status_label"))
        self.assertEqual(self.editor.status_label.pack_info().get("side"), "bottom")


if __name__ == '__main__':
    unittest.main()
