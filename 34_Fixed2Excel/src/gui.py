import logging
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_context import create_context
from src.mapping_editor_window import MappingEditorWindow
from src.utils.logger import setup_logger
from src.handlers import diff_checker, excel_to_fixed, fixed_to_excel, mapping_handler, setup_handler


class QueueLogHandler(logging.Handler):
    """バックグラウンドスレッドのログをqueue経由でメインスレッドへ渡す"""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        tag = getattr(record, "tag", record.levelname)
        self.log_queue.put((tag, self.format(record)))


LOG_TAG_COLORS = {
    "INFO": "#1a1a1a",
    "WARNING": "#b36b00",
    "ERROR": "#c0392b",
    "START": "#0969da",
    "END": "#1a7f37",
    "DIFF": "#8250df",
}

# 実行頻度が低い操作は、押す前に「どんなときに使うか」を確認する
CONFIRM_MESSAGES = {
    "init": (
        "環境初期化はどんなとき？",
        "初回セットアップ時、または data/configs・data/input 等のフォルダを\n"
        "作り直したいときに実行します。\n"
        "既存のサンプルファイルは上書きしません（未作成のものだけ生成します）。\n\n"
        "実行しますか？",
    ),
    "mapping": (
        "mapping.csv更新はどんなとき？",
        "input内に新しい種類の固定長ファイルを追加したときに実行します。\n"
        "既存の対応関係は保持され、新規ファイル分だけ追記されます\n"
        "（実行前に既存のmapping.csvを自動でバックアップします）。\n\n"
        "実行しますか？",
    ),
}


class Fixed2ExcelApp(tk.Tk):
    # よく使う変換操作: 押しやすい上部に大きめのボタンで配置
    PRIMARY_ACTIONS = [
        ("固定長テキスト → Excel 変換", "to_excel"),
        ("Excel → 固定長テキスト 復元", "to_fixed"),
        ("差分チェック（入力 vs 復元後）", "diff_check"),
    ]
    # 初回セットアップ等、使用頻度の低い操作: 下部に小さめでまとめ、実行前に確認する
    SETUP_ACTIONS = [
        ("環境初期化", "init"),
        ("mapping.csv 更新", "mapping"),
    ]
    # 各データフォルダをエクスプローラーで開くだけの操作: 処理中でも押せてよい
    FOLDER_ACTIONS = [
        ("設定(configs)", "configs"),
        ("入力(input)", "input"),
        ("出力(output)", "output"),
        ("復元後(recreated_input)", "recreated"),
    ]

    def __init__(self):
        super().__init__()
        self.title("34_Fixed2Excel")
        self.geometry("720x520")

        self.log_queue = queue.Queue()
        self.logger = self._build_logger()
        self.ctx = create_context(self.logger)
        self.is_running = False
        self._mapping_editors = []

        self._build_widgets()
        self.after(100, self._drain_log_queue)

    def _build_logger(self):
        # CUI(src/main.py)と同じ data/logs/ にも残す（ウィンドウ表示だけだと閉じた後に追えない）
        logger = setup_logger(name="app_gui")
        handler = QueueLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
        return logger

    def _build_widgets(self):
        style = ttk.Style(self)
        style.configure("Primary.TButton", font=("Yu Gothic UI", 11, "bold"), padding=(20, 14))
        style.configure("Setup.TButton", font=("Yu Gothic UI", 9), padding=(10, 6))

        self.buttons = {}

        primary_frame = ttk.Frame(self, padding=(10, 10, 10, 4))
        primary_frame.pack(fill="x")
        for label, action_key in self.PRIMARY_ACTIONS:
            btn = ttk.Button(
                primary_frame, text=label, style="Primary.TButton",
                command=lambda k=action_key: self._run_action(k),
            )
            btn.pack(side="left", expand=True, fill="x", padx=4)
            self.buttons[action_key] = btn

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=(6, 2))
        ttk.Label(self, text="初期セットアップ（通常は最初の1回だけ）", padding=(10, 0)).pack(anchor="w")

        setup_frame = ttk.Frame(self, padding=(10, 2, 10, 8))
        setup_frame.pack(fill="x")
        for label, action_key in self.SETUP_ACTIONS:
            btn = ttk.Button(
                setup_frame, text=label, style="Setup.TButton",
                command=lambda k=action_key: self._run_action(k),
            )
            btn.pack(side="left", padx=4)
            self.buttons[action_key] = btn

        edit_mapping_btn = ttk.Button(
            setup_frame, text="mapping.csv 編集", style="Setup.TButton",
            command=self._open_mapping_editor,
        )
        edit_mapping_btn.pack(side="left", padx=4)
        self.buttons["edit_mapping"] = edit_mapping_btn

        ttk.Label(self, text="フォルダを開く", padding=(10, 0)).pack(anchor="w")
        folder_frame = ttk.Frame(self, padding=(10, 2, 10, 8))
        folder_frame.pack(fill="x")
        for label, dir_key in self.FOLDER_ACTIONS:
            btn = ttk.Button(
                folder_frame, text=label, style="Setup.TButton",
                command=lambda k=dir_key: self._open_folder(k),
            )
            btn.pack(side="left", padx=4)
            # 処理中でも他のファイル操作と競合しない読み取り専用操作のため、self.buttonsには入れず
            # _set_runningでの無効化対象から外す（実行中でも押せてよい）。

        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 0)).pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(self, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        for level, color in LOG_TAG_COLORS.items():
            self.log_text.tag_configure(level, foreground=color)

    def _drain_log_queue(self):
        while True:
            try:
                level, message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            tag = level if level in LOG_TAG_COLORS else "INFO"
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n", tag)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.after(100, self._drain_log_queue)

    def _set_running(self, running):
        self.is_running = running
        state = "disabled" if running else "normal"
        for btn in self.buttons.values():
            btn.configure(state=state)
        self.status_var.set("実行中..." if running else "待機中")

        # すでに開いているmapping.csv編集ウィンドウも連動してロックする
        # （開いたまま別のバックグラウンド処理を実行すると、mapping.csvへの同時書き込みで
        # 片方の変更が消える事故になり得るため）
        self._mapping_editors = [w for w in self._mapping_editors if w.winfo_exists()]
        for editor in self._mapping_editors:
            editor.set_locked(running)
            if not running:
                # ロック中に「mapping.csv更新」等が行を追加している可能性があるため
                # 解除時に一覧を読み直す
                editor.refresh()

    def _open_mapping_editor(self):
        if self.is_running:
            return
        editor = MappingEditorWindow(self, self.ctx)
        self._mapping_editors.append(editor)

    def _open_folder(self, dir_key):
        path = os.path.abspath(self.ctx.dirs[dir_key])
        try:
            os.startfile(path)
        except OSError as exc:
            messagebox.showerror(
                "フォルダを開けません", f"{path}\n\n{exc}\n\n未作成の場合は先に環境初期化を実行してください。",
                parent=self,
            )

    def _run_action(self, action_key):
        if self.is_running:
            return

        confirm = CONFIRM_MESSAGES.get(action_key)
        if confirm and not messagebox.askyesno(*confirm, parent=self):
            return

        self._set_running(True)
        thread = threading.Thread(target=self._execute, args=(action_key,), daemon=True)
        thread.start()

    def _execute(self, action_key):
        try:
            if action_key == "init":
                setup_handler.init_environment(self.ctx)
            elif action_key == "mapping":
                mapping_handler.build_or_update_mapping(self.ctx)
            elif action_key == "to_excel":
                fixed_to_excel.convert_all(self.ctx)
            elif action_key == "to_fixed":
                excel_to_fixed.restore_all(self.ctx)
            elif action_key == "diff_check":
                diff_checker.check_all(self.ctx)
        except Exception:
            self.logger.exception("処理中にエラーが発生しました。")
        finally:
            self.after(0, self._set_running, False)


def main():
    app = Fixed2ExcelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
