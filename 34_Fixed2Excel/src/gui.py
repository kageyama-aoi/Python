import logging
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_context import create_context
from src.utils.logger import setup_logger
from src.handlers import excel_to_fixed, fixed_to_excel, mapping_handler, setup_handler


class QueueLogHandler(logging.Handler):
    """バックグラウンドスレッドのログをqueue経由でメインスレッドへ渡す"""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put((record.levelname, self.format(record)))


LOG_TAG_COLORS = {
    "INFO": "#1a1a1a",
    "WARNING": "#b36b00",
    "ERROR": "#c0392b",
}


class Fixed2ExcelApp(tk.Tk):
    ACTIONS = [
        ("環境初期化", "init"),
        ("mapping.csv 更新", "mapping"),
        ("固定長テキスト → Excel 変換", "to_excel"),
        ("Excel → 固定長テキスト 復元", "to_fixed"),
    ]

    def __init__(self):
        super().__init__()
        self.title("34_Fixed2Excel")
        self.geometry("720x480")

        self.log_queue = queue.Queue()
        self.logger = self._build_logger()
        self.ctx = create_context(self.logger)
        self.is_running = False

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
        button_frame = ttk.Frame(self, padding=10)
        button_frame.pack(fill="x")

        self.buttons = {}
        for label, action_key in self.ACTIONS:
            btn = ttk.Button(button_frame, text=label, command=lambda k=action_key: self._run_action(k))
            btn.pack(side="left", padx=4)
            self.buttons[action_key] = btn

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

    def _run_action(self, action_key):
        if self.is_running:
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
        except Exception:
            self.logger.exception("処理中にエラーが発生しました。")
        finally:
            self.after(0, self._set_running, False)


def main():
    app = Fixed2ExcelApp()
    app.mainloop()


if __name__ == "__main__":
    main()
