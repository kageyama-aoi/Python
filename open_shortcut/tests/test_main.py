import unittest
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch, MagicMock
import copy
import os
import sys

# プロジェクトのルートディレクトリをPythonのパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import DirectoryOpenerApp
from src.config_manager import ConfigManager

class TestDirectoryOpenerApp(unittest.TestCase):
    """
    DirectoryOpenerAppのGUIロジックをテストするクラス。
    """

    def setUp(self):
        """各テストの前に実行されるセットアップ処理。"""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        config_path = os.path.join(project_root, "data", "config.json")
        
        self.root = tk.Tk()
        self.root.withdraw()

        # ConfigManagerをDirectoryOpenerAppのインスタンス化の前にパッチする
        with patch('src.main.ConfigManager') as mock_cm_class:
            # セットアップのために実際のconfigを読み込むための本物のConfigManagerを作成
            real_cm = ConfigManager(config_path=config_path)
            self.config = real_cm.get_config()

            # 作成されるモックインスタンスを設定
            mock_instance = MagicMock()
            mock_instance.get_config.return_value = self.config
            mock_instance.reload.return_value = True # リロードは成功すると仮定
            
            # クラスがモックインスタンスを返すようにする
            mock_cm_class.return_value = mock_instance

            # DirectoryOpenerAppが作成されると、このモックを使用する
            self.app = DirectoryOpenerApp(self.root)
            # テストで使用できるようにモックを保存
            self.mock_config_manager = mock_instance

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理。"""
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

        expected_title = self.config["pages"][target_page_name]["window_title"]
        self.assertEqual(self.app.master.title(), expected_title, "ページ切り替え後のウィンドウタイトルが正しくありません。")
        self.assertIn(target_page_name, self.app.status_label.cget("text"), "ステータスバーのメッセージが正しくありません。")

    def test_dynamic_ui_reload(self):
        """動的リロード機能がUIを正しく再構築するかテストする。"""
        initial_button_text = "📁 Documents"
        initial_button = self.find_button_recursively(self.app.master, initial_button_text)
        self.assertIsNotNone(initial_button, f"初期状態のボタン '{initial_button_text}' が見つかりません。")

        modified_config = copy.deepcopy(self.config)
        
        found_and_modified = False
        for entry in modified_config["pages"]["main_menu"]["entries"]:
            if entry.get("name") == "Documents":
                entry["name"] = "My Documents"
                found_and_modified = True
                break
        self.assertTrue(found_and_modified, "テスト用の設定変更ができませんでした。config.jsonを確認してください。")
        
        # モックが次回のget_config呼び出しで新しいconfigを返すように設定
        # reloadメソッドは内部で新しいconfigを取得する
        self.mock_config_manager.get_config.return_value = modified_config
        
        # Act: UIリロードをトリガー
        self.app.reload_ui()

        # Assert: UIが正しく更新されたことを確認
        self.mock_config_manager.reload.assert_called_once()
        self.assertIsNone(self.find_button_recursively(self.app.master, initial_button_text), f"古いボタン '{initial_button_text}' がUIに残っています。")
        self.assertIsNotNone(self.find_button_recursively(self.app.master, "📁 My Documents"), "新しいボタン '📁 My Documents' が作成されていません。")

if __name__ == '__main__':
    unittest.main()