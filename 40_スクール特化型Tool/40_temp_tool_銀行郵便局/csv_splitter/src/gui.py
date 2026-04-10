import io
import json
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, str(Path(__file__).parent))
from run import split_csv

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.json"

ENCODINGS = ["utf-8", "shift_jis", "cp932", "utf-8-sig"]


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rows_per_file": 10000, "encoding": "utf-8", "has_header": True, "delimiter": ""}


def _save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class QueueStream(io.TextIOBase):
    """print() の出力をキューに流す擬似ストリーム。"""

    def __init__(self, q: queue.Queue) -> None:
        self._q = q

    def write(self, s: str) -> int:
        if s:
            self._q.put(s)
        return len(s)

    def flush(self) -> None:
        pass


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CSV Splitter")
        self.resizable(False, False)

        self._log_queue: queue.Queue = queue.Queue()
        self._build_ui()
        self._load_config_to_form()
        self._poll_log()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 4}

        # --- 入力ファイル ---
        frm_file = ttk.LabelFrame(self, text="入力ファイル")
        frm_file.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)

        self._var_file = tk.StringVar()
        ttk.Entry(frm_file, textvariable=self._var_file, width=50).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(frm_file, text="参照...", command=self._browse_file).grid(row=0, column=1, padx=6, pady=4)

        # --- 設定 ---
        frm_cfg = ttk.LabelFrame(self, text="設定")
        frm_cfg.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

        ttk.Label(frm_cfg, text="分割行数").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self._var_rows = tk.StringVar()
        ttk.Entry(frm_cfg, textvariable=self._var_rows, width=12).grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm_cfg, text="エンコーディング").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self._var_enc = tk.StringVar()
        ttk.Combobox(frm_cfg, textvariable=self._var_enc, values=ENCODINGS, width=14, state="readonly").grid(
            row=1, column=1, sticky="w", padx=6, pady=4
        )

        ttk.Label(frm_cfg, text="デリミタ（空=自動）").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self._var_delim = tk.StringVar()
        ttk.Entry(frm_cfg, textvariable=self._var_delim, width=6).grid(row=2, column=1, sticky="w", padx=6, pady=4)

        self._var_header = tk.BooleanVar()
        ttk.Checkbutton(frm_cfg, text="ヘッダーあり（各分割ファイルに複製）", variable=self._var_header).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=6, pady=4
        )

        # --- 実行 ---
        self._btn_run = ttk.Button(self, text="実行", command=self._run)
        self._btn_run.grid(row=2, column=0, columnspan=2, pady=8)

        # --- ログ ---
        frm_log = ttk.LabelFrame(self, text="ログ")
        frm_log.grid(row=3, column=0, columnspan=2, sticky="nsew", **pad)

        self._log_text = tk.Text(frm_log, width=70, height=14, state="disabled", wrap="word")
        self._log_text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frm_log, command=self._log_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._log_text.configure(yscrollcommand=sb.set)

    # ------------------------------------------------------------------
    # config読み書き
    # ------------------------------------------------------------------

    def _load_config_to_form(self) -> None:
        cfg = _load_config()
        self._var_rows.set(str(cfg.get("rows_per_file", 10000)))
        enc = cfg.get("encoding", "utf-8")
        self._var_enc.set(enc if enc in ENCODINGS else ENCODINGS[0])
        self._var_header.set(bool(cfg.get("has_header", True)))
        self._var_delim.set(cfg.get("delimiter") or "")

    def _form_to_config(self) -> dict:
        return {
            "rows_per_file": int(self._var_rows.get()),
            "encoding": self._var_enc.get(),
            "has_header": self._var_header.get(),
            "delimiter": self._var_delim.get() or None,
        }

    # ------------------------------------------------------------------
    # ファイル選択
    # ------------------------------------------------------------------

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSV / TSV", "*.csv *.tsv"), ("すべてのファイル", "*.*")],
        )
        if path:
            self._var_file.set(path)

    # ------------------------------------------------------------------
    # 実行
    # ------------------------------------------------------------------

    def _run(self) -> None:
        file_str = self._var_file.get().strip()
        if not file_str:
            messagebox.showwarning("入力エラー", "入力ファイルを選択してください。")
            return

        try:
            cfg = self._form_to_config()
        except ValueError:
            messagebox.showwarning("入力エラー", "分割行数は整数で入力してください。")
            return

        _save_config(cfg)
        self._btn_run.configure(state="disabled")
        self._log_append("")

        threading.Thread(
            target=self._run_worker,
            args=(Path(file_str), cfg),
            daemon=True,
        ).start()

    def _run_worker(self, input_path: Path, cfg: dict) -> None:
        tmp_config = BASE_DIR / ".tmp_gui_config.json"
        started_at = datetime.now()
        delim_disp = repr(cfg.get("delimiter")) if cfg.get("delimiter") else "自動検出"

        header = (
            "━" * 50 + "\n"
            f"  開始時刻  : {started_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  ファイル  : {input_path}\n"
            f"  分割行数  : {cfg['rows_per_file']:,} 行\n"
            f"  エンコード: {cfg['encoding']}\n"
            f"  デリミタ  : {delim_disp}\n"
            f"  ヘッダー  : {'あり' if cfg['has_header'] else 'なし'}\n"
            "━" * 50 + "\n"
        )
        self._log_queue.put(header)

        error_msg = ""
        try:
            with open(tmp_config, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False)

            orig_stdout = sys.stdout
            sys.stdout = QueueStream(self._log_queue)
            try:
                split_csv(input_path, tmp_config)
            finally:
                sys.stdout = orig_stdout
        except Exception as e:
            error_msg = str(e)
            self._log_queue.put(f"[ERROR] {e}\n")
        finally:
            if tmp_config.exists():
                tmp_config.unlink()

            ended_at = datetime.now()
            elapsed = ended_at - started_at
            total_sec = int(elapsed.total_seconds())
            elapsed_str = f"{total_sec // 60}分{total_sec % 60}秒" if total_sec >= 60 else f"{total_sec}秒"
            status = "ERROR" if error_msg else "SUCCESS"

            footer = (
                "━" * 50 + "\n"
                f"  終了時刻  : {ended_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  経過時間  : {elapsed_str}\n"
                f"  ステータス: {status}\n"
            )
            if error_msg:
                footer += f"  エラー    : {error_msg}\n"
            footer += "━" * 50 + "\n"

            self._log_queue.put(footer)
            self._log_queue.put(None)  # 完了シグナル

    # ------------------------------------------------------------------
    # ログ
    # ------------------------------------------------------------------

    def _log_append(self, text: str) -> None:
        self._log_text.configure(state="normal")
        self._log_text.insert("end", text)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _poll_log(self) -> None:
        try:
            while True:
                item = self._log_queue.get_nowait()
                if item is None:
                    self._btn_run.configure(state="normal")
                else:
                    self._log_append(item)
        except queue.Empty:
            pass
        self.after(100, self._poll_log)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
