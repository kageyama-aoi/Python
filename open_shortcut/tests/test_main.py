import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
import os
import sys

# プロジェクトのルートディレクトリをPythonのパスに追加
# これにより、`src`パッケージを正しくインポートできる
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import DirectoryOpenerApp

class TestDirectoryOpenerApp(unittest.TestCase):
    """
    DirectoryOpenerAppのGUIロジックをテストするクラス。
    """

    def setUp(self):
        """各テストの前に実行されるセットアップ処理。"""
        # テスト実行時のパスの問題を解決するため、設定ファイルのパスを絶対パスに書き換える
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        # DirectoryOpenerAppクラスが持つCONFIG_FILEの値を、このテスト実行中だけ絶対パスに上書きする
        DirectoryOpenerApp.CONFIG_FILE = os.path.join(project_root, "data", "config.json")

        self.root = tk.Tk()
        # テスト実行中にGUIウィンドウが表示されるのを防ぐ
        self.root.withdraw()
        self.app = DirectoryOpenerApp(self.root)

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理。"""
        # テストウィンドウが残らないように破棄する
        if self.root.winfo_exists():
            self.root.destroy()

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

    def test_app_initialization_and_page_display(self):
        """アプリケーションが正常に初期化され、初期ページが表示されることをテストする。"""
        self.assertIsNotNone(self.app, "アプリケーションオブジェクトが作成されていません。")
        
        # config.jsonのinitial_pageとwindow_titleに基づいてタイトルを検証
        initial_page_config = self.app.config["pages"]["main_menu"]
        expected_title = initial_page_config.get("window_title")
        self.assertEqual(self.app.master.title(), expected_title, "初期ウィンドウのタイトルが正しくありません。")

    @patch('os.startfile')
    def test_open_directory_button_click(self, mock_startfile):
        """「ディレクトリを開く」ボタンが正しくos.startfileを呼び出すかテストする。"""
        # テスト対象のボタン情報 (config.jsonに依存)
        button_name = "Documents"
        button_display_text = f"📁 {button_name}"
        expected_path = "C:\\Users\\kageyama\\Documents"

        # GUIからボタンウィジェットを探す
        button = self.find_button_recursively(self.app.page_container, button_display_text)
        self.assertIsNotNone(button, f"ボタン '{button_display_text}' が見つかりません。")

        # ボタンのクリックをシミュレート
        button.invoke()

        # os.startfileが正しいパスで1回だけ呼び出されたことを検証
        mock_startfile.assert_called_once_with(os.path.expandvars(expected_path))
        self.assertIn(button_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

    @patch('webbrowser.open_new_tab')
    def test_open_url_button_click(self, mock_open_new_tab):
        """「URLを開く」ボタンが正しくwebbrowser.open_new_tabを呼び出すかテストする。"""
        button_name = "各種リンク"
        button_display_text = f"🌐 {button_name}"
        expected_url = "https://docs.google.com/spreadsheets/d/1TfI1uucI9zAlgTnCESs4gsvt_EoAQYQzbY219zMowRA/edit?gid=0#gid=0"

        button = self.find_button_recursively(self.app.page_container, button_display_text)
        self.assertIsNotNone(button, f"ボタン '{button_display_text}' が見つかりません。")

        button.invoke()

        mock_open_new_tab.assert_called_once_with(expected_url)
        self.assertIn(button_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

    def test_show_page_button_click(self):
        """「ページ切り替え」ボタンが正しくページを切り替えるかテストする。"""
        button_display_text = "→ テストメニューへ"
        target_page_name = "test_tframe"

        button = self.find_button_recursively(self.app.page_container, button_display_text)
        self.assertIsNotNone(button, f"ボタン '{button_display_text}' が見つかりません。")

        button.invoke()

        # ページが切り替わった結果、ウィンドウタイトルが変更されたことを検証
        expected_title = self.app.config["pages"][target_page_name]["window_title"]
        self.assertEqual(self.app.master.title(), expected_title, "ページ切り替え後のウィンドウタイトルが正しくありません。")
        self.assertIn(target_page_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

if __name__ == '__main__':
    unittest.main()