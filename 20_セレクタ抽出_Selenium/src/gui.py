import tkinter as tk
from tkinter import messagebox
import threading
from . import config
from .browser_manager import BrowserManager

class Application(tk.Tk):
    """メインGUIアプリケーションクラス"""
    
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry(config.WINDOW_SIZE)
        
        self.setup_ui()

    def setup_ui(self):
        # URL入力エリア
        tk.Label(self, text="調査対象URL:").pack(pady=(10, 0))
        self.url_entry = tk.Entry(self, width=50)
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, config.DEFAULT_URL)

        # モード選択エリア
        tk.Label(self, text="動作モード:").pack(pady=(10, 0))
        self.mode_var = tk.StringVar(value=config.DEFAULT_MODE)
        frame_mode = tk.Frame(self)
        frame_mode.pack()
        tk.Radiobutton(frame_mode, text="ポップアップ表示", variable=self.mode_var, value="popup").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_mode, text="ログ出力", variable=self.mode_var, value="log").pack(side=tk.LEFT, padx=10)

        # オプションエリア
        self.prevent_nav_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="リンク遷移・ボタン動作をブロックする", variable=self.prevent_nav_var).pack(pady=5)

        # 起動ボタン
        tk.Button(self, text="ブラウザ起動", command=self.on_start, bg="#dddddd", height=2).pack(pady=10)

    def on_start(self):
        selected_mode = self.mode_var.get()
        target_url = self.url_entry.get().strip()
        is_prevent = self.prevent_nav_var.get()

        if not target_url:
            messagebox.showwarning("入力エラー", config.MSG_URL_EMPTY)
            return
        
        # GUIスレッドをブロックしないように別スレッドで実行
        threading.Thread(
            target=lambda: self.launch_browser_thread(selected_mode, target_url, is_prevent), 
            daemon=True
        ).start()

    def launch_browser_thread(self, mode, url, prevent_nav):
        manager = BrowserManager(mode=mode, initial_url=url, prevent_navigation=prevent_nav)
        manager.start()
