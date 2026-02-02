"""Tkinterでアプリ本体を組み立てるエントリモジュール。"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from .settings_editor import SettingsEditor
from .config_manager import ConfigManager
from .action_handler import ActionHandler
from .ui_builder import UIBuilder
from . import constants as C

class DirectoryOpenerApp:
    """
    設定ファイルに基づいてディレクトリやURLを開くボタンを動的に生成する
    Tkinter GUIアプリケーション。
    複数ページの切り替えに対応。
    """
    def __init__(self, master: tk.Tk):
        """アプリケーションを初期化し、UIを構築する。"""
        self.master = master
        self.icon_images = {}  # PhotoImageオブジェクトを保持 (ガベージコレクション対策)
        self.style = ttk.Style()
        self.dynamic_style_counter = 0
        self.pages = {}
        self._after_id = None # UIリロードのスケジュールID

        # --- Core Components ---
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        if not self.config:
            master.destroy()  # 設定がなければウィンドウを閉じる
            return
            
        self.action_handler = ActionHandler(self)
        
        # --- Main UI Containers (created once) ---
        self.page_container = ttk.Frame(self.master)
        self.page_container.pack(fill=tk.BOTH, expand=True)
        self.status_label = ttk.Label(self.master, text="準備完了", style="Status.TLabel", anchor=tk.W, padding=(10, 5, 10, 5))
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
        self.settings_button = ttk.Button(self.master, text="設定", command=self.open_settings_window)
        self.settings_button.pack(side=tk.RIGHT, anchor=tk.SE, padx=10, pady=5)

        self.ui_builder = UIBuilder(self, self.page_container, self.status_label, self.settings_button)

        # --- UI Setup ---
        self._setup_window()
        self._setup_styles()
        self.ui_builder.create_widgets_content()

        # 初期ページを表示
        initial_page = self.config.get(C.ConfigKey.SETTINGS, {}).get(C.ConfigKey.INITIAL_PAGE, "home")
        self.show_page(initial_page)

    def _setup_window(self):
        """ウィンドウのタイトル、サイズ、アイコンなどを設定する。"""
        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        self.master.title(settings.get(C.ConfigKey.WINDOW_TITLE, "Directory Opener"))
        self.master.geometry(settings.get(C.ConfigKey.GEOMETRY, "400x450"))
        
        resizable = settings.get(C.ConfigKey.RESIZABLE, [False, True])
        self.master.resizable(resizable[0], resizable[1])

        # ウィンドウアイコンの設定
        icon_folder = settings.get(C.ConfigKey.ICON_FOLDER, "icons")
        window_icon = settings.get(C.ConfigKey.WINDOW_ICON)
        if window_icon:
            window_icon_path = os.path.join(icon_folder, window_icon)
            if os.path.exists(window_icon_path):
                try:
                    self.master.iconbitmap(window_icon_path)
                except tk.TclError:
                    print(f"警告: ウィンドウアイコンを読み込めませんでした: {window_icon_path}")

    def _setup_styles(self):
        """ttkウィジェットのスタイルを設定する。"""
        styles_config = self.config.get(C.ConfigKey.STYLES, {})
        for style_name, options in styles_config.items():
            self.style.configure(style_name, **options)

    def reload_ui(self):
        """
        UIの再読み込みをスケジュールします。
        もし既にスケジュールされている再読み込みがあればキャンセルし、
        新しい再読み込みをスケジュールすることで、連続した呼び出しを一度にまとめます。
        """
        if self._after_id:
            self.master.after_cancel(self._after_id)
        
        self._after_id = self.master.after(10, self._perform_reload)

    def _perform_reload(self):
        """UIを再読み込みする実際の処理。"""
        # スケジュールIDをリセット
        self._after_id = None

        # Ensure all pending events are processed before destroying widgets
        self.master.update_idletasks() # Added for robustness

        # 1. Clear content of main containers
        for widget in list(self.page_container.winfo_children()):
            widget.destroy()
        self.page_container.pack_forget() # 一度アンパックして再パック

        # Reset internal state before rebuilding
        self.pages = {}
        self.icon_images = {}
        self.dynamic_style_counter = 0

        # 3. Reload config
        if not self.config_manager.reload():
            self.master.destroy()
            return
        self.config = self.config_manager.get_config()
        self.ui_builder.config = self.config

        # 4. Re-create UI content
        self._setup_window()
        self._setup_styles()
        self.page_container.pack(fill=tk.BOTH, expand=True) # 再パック
        self.ui_builder.create_widgets_content() # UIBuilderを使ってコンテンツを再構築
        
        # 5. Show initial page
        initial_page = self.config.get(C.ConfigKey.SETTINGS, {}).get(C.ConfigKey.INITIAL_PAGE, "home")
        self.show_page(initial_page)
        
        print("UI reloaded successfully.")

    def show_page(self, page_name: str):
        """指定された名前のページを表示し、ウィンドウタイトルを更新する。"""
        page = self.pages.get(page_name)
        if page:
            for p in self.pages.values():
                p.pack_forget()
            page.pack(fill=tk.BOTH, expand=True)
            
            page_title = self.config.get(C.ConfigKey.PAGES, {}).get(page_name, {}).get(C.ConfigKey.WINDOW_TITLE)
            global_title = self.config.get(C.ConfigKey.SETTINGS, {}).get(C.ConfigKey.WINDOW_TITLE, "Directory Opener")
            self.master.title(page_title or global_title)
            
            self.status_label.config(text=f"「{page_name}」ページを表示しました。")
        else:
            messagebox.showwarning("警告", f"ページ '{page_name}' が見つかりません。")
            self.status_label.config(text=f"エラー: ページ '{page_name}' の表示に失敗しました。")

    def open_settings_window(self):
        """設定画面を新しいウィンドウで開く。"""
        settings_window = SettingsEditor(self.master, self.config_manager, on_save_callback=self.reload_ui)
        settings_window.grab_set() # モーダルウィンドウにする

def main():
    """アプリケーションを起動する。"""
    root = tk.Tk()
    app = DirectoryOpenerApp(root)
    if root.winfo_exists():
        root.mainloop()

if __name__ == "__main__":
    main()
