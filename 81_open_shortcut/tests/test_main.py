"""Tkinter UIを使ってDirectoryOpenerAppを検証するテスト群。"""

import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch, MagicMock
import os
import sys
import json
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# プロジェクトのルートディレクトリをPythonのパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import DirectoryOpenerApp
from src.config_manager import ConfigManager

# テストデータへのパス
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
INITIAL_CONFIG_PATH = os.path.join(TEST_DATA_DIR, 'test_config_initial.json')
MODIFIED_CONFIG_PATH = os.path.join(TEST_DATA_DIR, 'test_config_modified.json')


class TestDirectoryOpenerApp(unittest.TestCase):
    """
    DirectoryOpenerAppのGUIロジックをテストするクラス。
    """
    @classmethod
    def setUpClass(cls):
        """クラスの全テストの前に一度だけ実行されるセットアップ。"""
        cls.patcher = patch('src.main.ConfigManager')
        cls.mock_cm_class = cls.patcher.start()

    @classmethod
    def tearDownClass(cls):
        """クラスの全テストの後に一度だけ実行されるクリーンアップ。"""
        cls.patcher.stop()

    def setUp(self):
        """各テストの前に実行されるセットアップ処理。"""
        logging.info("Setting up test: %s", self.id())
        
        self.root = tk.Tk()
        self.root.withdraw()

        # テスト用の初期設定ファイルを読み込む
        with open(INITIAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # モックインスタンスを設定
        # setUpClassでモック化されたクラスからインスタンスを作成
        mock_instance = MagicMock()
        mock_instance.get_config.return_value = self.config
        mock_instance.reload.return_value = True
        
        # クラスがモックインスタンスを返すようにする
        self.mock_cm_class.return_value = mock_instance

        # DirectoryOpenerAppが作成されると、このモックを使用する
        self.app = DirectoryOpenerApp(self.root)
        # テストで使用できるようにモックを保存
        self.mock_config_manager = mock_instance
        logging.info("Test setup complete.")

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理。"""
        logging.info("Tearing down test: %s", self.id())
        if self.root.winfo_exists():
            self.root.destroy()
        logging.info("Test teardown complete.")

    # --- Custom Assertions ---
    def assertButtonExists(self, button_text, msg=None):
        """指定されたテキストを持つボタンが存在することを検証する。"""
        if not self.find_button_recursively(self.app.master, button_text):
            self.fail(self._formatMessage(msg, f"Button with text '{button_text}' not found."))

    def assertButtonNotExists(self, button_text, msg=None):
        """指定されたテキストを持つボタンが存在しないことを検証する。"""
        widget = self.find_button_recursively(self.app.master, button_text)
        if widget:
            all_widgets = self.get_all_widgets_repr(self.app.master)
            self.fail(self._formatMessage(msg, f"Button with text '{button_text}' was found unexpectedly.\nExisting widgets:\n{all_widgets}"))

    # --- Helper Methods ---
    def find_button_recursively(self, parent_widget, button_text_to_find):
        """
        指定されたウィジェットの子を再帰的に探索し、
        指定されたテキストを持つボタンウィジェットを見つける。
        """
        for widget in parent_widget.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget("text") == button_text_to_find:
                return widget
            
            found_widget = self.find_button_recursively(widget, button_text_to_find)
            if found_widget:
                return found_widget
        return None

    def get_all_widgets_repr(self, parent_widget, indent=0):
        """デバッグ用に全ウィジェットの情報を文字列として取得する。"""
        result = ""
        for widget in parent_widget.winfo_children():
            result += "  " * indent + repr(widget) + "\n"
            result += self.get_all_widgets_repr(widget, indent + 1)
        return result

    # --- Tests ---
    def test_app_initialization_and_page_display(self):
        """アプリケーションが正常に初期化され、初期ページが表示されることをテストする。"""
        self.assertIsNotNone(self.app, "アプリケーションオブジェクトが作成されていません。")
        
        initial_page_config = self.config["pages"]["main_menu"]
        expected_title = initial_page_config.get("window_title")
        self.assertEqual(self.app.master.title(), expected_title, "初期ウィンドウのタイトルが正しくありません。")

    @patch('os.startfile')
    def test_open_directory_button_click(self, mock_startfile):
        """「ディレクトリを開く」ボタンが正しくos.startfileを呼び出すかテストする。"""
        button_name = "Documents"
        button_display_text = f"📁 {button_name}"
        expected_path = "C:\\Users\\kageyama\\Documents"

        button = self.find_button_recursively(self.app.page_container, button_display_text)
        self.assertIsNotNone(button, f"ボタン '{button_display_text}' が見つかりません。")

        button.invoke()

        mock_startfile.assert_called_once_with(os.path.expandvars(expected_path))
        self.assertIn(button_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

    @patch('webbrowser.open_new_tab')
    def test_open_url_button_click(self, mock_open_new_tab):
        """「URLを開く」ボタンが正しくwebbrowser.open_new_tabを呼び出すかテストする。"""
        button_name = "各種リンク"
        button_display_text = f"🌐 {button_name}"
        expected_url = "https://example.com/links"

        button = self.find_button_recursively(self.app.page_container, button_display_text)
        self.assertIsNotNone(button, f"ボタン '{button_display_text}' が見つかりません。")

        button.invoke()

        mock_open_new_tab.assert_called_once_with(expected_url)
        self.assertIn(button_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

    def test_show_page_button_click(self):
        """「ページ切り替え」ボタンが正しくページを切り替えるかテストする。"""
        button_display_text = "→ テストメニューへ"
        target_page_name = "sub_menu"

        button = self.find_button_recursively(self.app.page_container, button_display_text)
        self.assertIsNotNone(button, f"ボタン '{button_display_text}' が見つかりません。")

        button.invoke()

        expected_title = self.config["pages"][target_page_name]["window_title"]
        self.assertEqual(self.app.master.title(), expected_title, "ページ切り替え後のウィンドウタイトルが正しくありません。")
        self.assertIn(target_page_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

    def test_menu_order_reverse_displays_entries_in_reverse(self):
        """menu_order=reverse のとき、メニュー項目が逆順で表示されることをテストする。"""
        self.config["settings"]["menu_order"] = "reverse"

        # reverse設定を反映した新しいアプリを作成
        if self.root.winfo_exists():
            self.root.destroy()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = DirectoryOpenerApp(self.root)

        main_page = self.app.pages["main_menu"]
        button_texts = [
            widget.cget("text")
            for widget in main_page.winfo_children()
            if isinstance(widget, ttk.Button)
        ]

        self.assertTrue(button_texts, "メインメニューにボタンが表示されていません。")
        self.assertEqual(button_texts[0], "📁 経費精算書", "逆順表示時の先頭ボタンが期待と異なります。")

    def test_page_menu_order_overrides_global_setting(self):
        """ページ個別menu_orderが全体settings.menu_orderより優先されることをテストする。"""
        self.config["settings"]["menu_order"] = "reverse"
        self.config["pages"]["main_menu"]["menu_order"] = "normal"

        if self.root.winfo_exists():
            self.root.destroy()
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = DirectoryOpenerApp(self.root)

        main_page = self.app.pages["main_menu"]
        button_texts = [
            widget.cget("text")
            for widget in main_page.winfo_children()
            if isinstance(widget, ttk.Button)
        ]

        self.assertTrue(button_texts, "メインメニューにボタンが表示されていません。")
        self.assertEqual(button_texts[0], "→ テストメニューへ", "ページ個別表示順が全体設定を上書きできていません。")

    def test_dynamic_ui_reload(self):
        """動的リロード機能がUIを正しく再構築するかテストする。"""
        initial_button_text = "📁 Documents"
        modified_button_text = "📁 My Documents"

        logging.info("--- dynamic_ui_reload: 実行前の状態 ---")
        self.assertButtonExists(initial_button_text, f"初期状態のボタン '{initial_button_text}' が見つかりません。")
        logging.info("初期ウィジェットツリー:\n%s", self.get_all_widgets_repr(self.app.master))

        # 変更後の設定ファイルを読み込む
        with open(MODIFIED_CONFIG_PATH, 'r', encoding='utf-8') as f:
            modified_config = json.load(f)
        
        # モックが次回のget_config呼び出しで新しいconfigを返すように設定
        self.mock_config_manager.get_config.return_value = modified_config
        
        # モックの呼び出しカウントをリセットし、テストのActフェーズでの呼び出しのみをカウント
        self.mock_config_manager.reload.reset_mock()
        
        # Act: UIリロードをトリガー
        logging.info("--- dynamic_ui_reload: self.app.reload_ui() を呼び出し ---")
        self.app.reload_ui()
        
        # Tkinterのイベントループを処理して、.after()でスケジュールされたコールバックを実行
        logging.info("--- dynamic_ui_reload: self.app.master.update() を呼び出し ---")
        self.app.master.update()

        logging.info("--- dynamic_ui_reload: self.app.reload_ui() 呼び出し完了 ---")

        # Assert: UIが正しく更新されたことを確認
        logging.info("リロード後のウィジェットツリー:\n%s", self.get_all_widgets_repr(self.app.master))
        # reload_uiの処理は1回のreloadで完結する。
        self.assertEqual(self.mock_config_manager.reload.call_count, 1, "ConfigManager.reload()の呼び出し回数が期待と異なります。")
        self.assertButtonNotExists(initial_button_text, f"古いボタン '{initial_button_text}' がUIに残っています。")
        self.assertButtonExists(modified_button_text, f"新しいボタン '{modified_button_text}' が作成されていません。")

if __name__ == '__main__':
    unittest.main()
