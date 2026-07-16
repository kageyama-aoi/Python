import json
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

sys.path.insert(0, str(Path(__file__).parent))
from analyze import (
    _count_rows,
    _detect_encoding_from_file,
    _fmt_size,
    _read_first_row,
    _suggest_rows,
)
from presets import load_presets, save_presets
from run import SplitOptions, _detect_delimiter, split_csv

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.json"

ENCODINGS = ["utf-8", "shift_jis", "cp932", "utf-8-sig"]

# ワーカースレッド→メインスレッドへの通知（すべて log_queue 経由で受け渡す）
_SENTINEL_SPLIT_DONE = object()
_SENTINEL_ANALYZE_DONE = object()
_SENTINEL_APPLY_ANALYSIS = object()  # ("payload": (encoding, delimiter)) をフォームに反映


# ------------------------------------------------------------------
# config読み書き
# ------------------------------------------------------------------

def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"rows_per_file": 10000, "encoding": "utf-8", "has_header": True, "delimiter": ""}


def _save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------
# App
# ------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CSV Splitter")
        self.resizable(False, False)

        self._log_queue: queue.Queue = queue.Queue()
        self._presets: dict = {}
        self._build_ui()
        self._load_config_to_form()
        self._refresh_presets()
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
        ttk.Entry(frm_file, textvariable=self._var_file, width=46).grid(row=0, column=0, padx=6, pady=4)
        ttk.Button(frm_file, text="参照...", command=self._browse_file).grid(row=0, column=1, padx=(0, 4), pady=4)
        self._btn_analyze = ttk.Button(frm_file, text="解析", command=self._analyze)
        self._btn_analyze.grid(row=0, column=2, padx=(0, 6), pady=4)

        # --- 設定 ---
        frm_cfg = ttk.LabelFrame(self, text="設定")
        frm_cfg.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

        ttk.Label(frm_cfg, text="お気に入り").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self._var_preset = tk.StringVar()
        self._cmb_preset = ttk.Combobox(
            frm_cfg, textvariable=self._var_preset, width=24, state="readonly"
        )
        self._cmb_preset.grid(row=0, column=1, sticky="w", padx=6, pady=4)
        self._cmb_preset.bind("<<ComboboxSelected>>", self._on_preset_selected)

        frm_preset_btns = ttk.Frame(frm_cfg)
        frm_preset_btns.grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        ttk.Button(frm_preset_btns, text="保存...", width=7, command=self._save_preset).pack(side="left", padx=(0, 4))
        ttk.Button(frm_preset_btns, text="削除", width=5, command=self._delete_preset).pack(side="left")

        ttk.Label(frm_cfg, text="分割行数").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self._var_rows = tk.StringVar()
        ttk.Entry(frm_cfg, textvariable=self._var_rows, width=12).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(frm_cfg, text="エンコーディング").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self._var_enc = tk.StringVar()
        ttk.Combobox(frm_cfg, textvariable=self._var_enc, values=ENCODINGS, width=14, state="readonly").grid(
            row=2, column=1, sticky="w", padx=6, pady=4
        )

        ttk.Label(frm_cfg, text="デリミタ（空=自動）").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        self._var_delim = tk.StringVar()
        ttk.Entry(frm_cfg, textvariable=self._var_delim, width=6).grid(row=3, column=1, sticky="w", padx=6, pady=4)

        self._var_header = tk.BooleanVar()
        ttk.Checkbutton(frm_cfg, text="ヘッダーあり（各分割ファイルに複製）", variable=self._var_header).grid(
            row=4, column=0, columnspan=3, sticky="w", padx=6, pady=4
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

    def _form_to_options(self) -> SplitOptions:
        return SplitOptions(
            rows_per_file=int(self._var_rows.get()),
            encoding=self._var_enc.get(),
            has_header=self._var_header.get(),
            delimiter=self._var_delim.get() or None,
        )

    # ------------------------------------------------------------------
    # お気に入り（プリセット）
    # ------------------------------------------------------------------

    def _refresh_presets(self, select: str | None = None) -> None:
        try:
            self._presets = load_presets()
        except (ValueError, OSError) as exc:
            messagebox.showerror("プリセット読み込みエラー", str(exc))
            self._presets = {}
        names = list(self._presets)
        self._cmb_preset["values"] = names
        if select in names:
            self._var_preset.set(select)
        elif self._var_preset.get() not in names:
            self._var_preset.set("")

    def _on_preset_selected(self, _event=None) -> None:
        name = self._var_preset.get()
        preset = self._presets.get(name)
        if not preset:
            return
        self._var_rows.set(str(preset.get("rows_per_file", 10000)))
        enc = preset.get("encoding", "utf-8")
        self._var_enc.set(enc if enc in ENCODINGS else ENCODINGS[0])
        self._var_header.set(bool(preset.get("has_header", True)))
        self._var_delim.set(preset.get("delimiter") or "")
        self._log_append(f"プリセット「{name}」を適用しました\n")

    def _save_preset(self) -> None:
        try:
            options = self._form_to_options()
        except ValueError:
            messagebox.showwarning("入力エラー", "分割行数は整数で入力してください。")
            return
        name = simpledialog.askstring(
            "お気に入り保存",
            "プリセット名を入力してください:",
            initialvalue=self._var_preset.get(),
            parent=self,
        )
        if name is None:
            return
        name = name.strip()
        if not name:
            return
        if name in self._presets and not messagebox.askyesno(
            "確認", f"プリセット「{name}」は既に存在します。上書きしますか？"
        ):
            return
        self._presets[name] = {
            "rows_per_file": options.rows_per_file,
            "encoding": options.encoding,
            "has_header": options.has_header,
            "delimiter": options.delimiter,
        }
        try:
            save_presets(self._presets)
        except OSError as exc:
            messagebox.showerror("エラー", f"プリセットの保存に失敗しました:\n{exc}")
            return
        self._refresh_presets(select=name)
        self._log_append(f"プリセット「{name}」を保存しました\n")

    def _delete_preset(self) -> None:
        name = self._var_preset.get()
        if not name:
            messagebox.showinfo("情報", "削除するプリセットを選択してください。")
            return
        if not messagebox.askyesno("確認", f"プリセット「{name}」を削除しますか？"):
            return
        self._presets.pop(name, None)
        try:
            save_presets(self._presets)
        except OSError as exc:
            messagebox.showerror("エラー", f"プリセットの保存に失敗しました:\n{exc}")
            return
        self._var_preset.set("")
        self._refresh_presets()
        self._log_append(f"プリセット「{name}」を削除しました\n")

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
    # ファイル解析
    # ------------------------------------------------------------------

    def _analyze(self) -> None:
        file_str = self._var_file.get().strip()
        if not file_str:
            messagebox.showwarning("入力エラー", "入力ファイルを選択してください。")
            return

        self._btn_analyze.configure(state="disabled")
        self._btn_run.configure(state="disabled")
        self._log_append("解析中...\n")

        threading.Thread(
            target=self._analyze_worker,
            args=(Path(file_str),),
            daemon=True,
        ).start()

    def _analyze_worker(self, path: Path) -> None:
        """バックグラウンドスレッド。UIへの反映はすべて log_queue 経由で行う。"""
        try:
            size_str = _fmt_size(path.stat().st_size)
            detected_enc = _detect_encoding_from_file(path)
            detected_delim = _detect_delimiter(path, detected_enc if detected_enc != "不明" else "utf-8", path.suffix)
            total_rows = _count_rows(path)
            col_count, header_preview = _read_first_row(
                path,
                detected_enc if detected_enc != "不明" else "utf-8",
                detected_delim,
            )

            delim_disp = {",": "カンマ (,)", "\t": "タブ (\\t)", ";": "セミコロン (;)"}.get(
                detected_delim, repr(detected_delim)
            )
            suggested = _suggest_rows(total_rows)

            result = (
                "━" * 50 + "\n"
                "  ファイル解析結果\n"
                "━" * 50 + "\n"
                f"  ファイルサイズ : {size_str}\n"
                f"  総行数         : {total_rows:,} 行\n"
                f"  検出エンコード : {detected_enc}\n"
                f"  検出デリミタ   : {delim_disp}\n"
                f"  カラム数       : {col_count}\n"
                f"  先頭行         : {header_preview}\n"
                f"  推奨分割行数   : {suggested}\n"
                "━" * 50 + "\n"
            )
            self._log_queue.put(result)
            self._log_queue.put((_SENTINEL_APPLY_ANALYSIS, detected_enc, detected_delim))

        except Exception as e:
            self._log_queue.put(f"[解析エラー] {e}\n")
        finally:
            self._log_queue.put(_SENTINEL_ANALYZE_DONE)

    def _apply_analysis(self, enc: str, delim: str) -> None:
        if enc in ENCODINGS:
            self._var_enc.set(enc)
        # カンマ・タブは「自動検出」に任せるのが自然なのでフォームには反映しない
        # 明示的に設定したい場合のみ書き込む（セミコロン等）
        if delim not in (",", "\t"):
            self._var_delim.set(delim)

    # ------------------------------------------------------------------
    # 実行
    # ------------------------------------------------------------------

    def _run(self) -> None:
        file_str = self._var_file.get().strip()
        if not file_str:
            messagebox.showwarning("入力エラー", "入力ファイルを選択してください。")
            return

        try:
            options = self._form_to_options()
        except ValueError:
            messagebox.showwarning("入力エラー", "分割行数は整数で入力してください。")
            return

        _save_config(
            {
                "rows_per_file": options.rows_per_file,
                "encoding": options.encoding,
                "has_header": options.has_header,
                "delimiter": options.delimiter,
            }
        )
        self._btn_run.configure(state="disabled")
        self._btn_analyze.configure(state="disabled")

        threading.Thread(
            target=self._run_worker,
            args=(Path(file_str), options),
            daemon=True,
        ).start()

    def _run_worker(self, input_path: Path, options: SplitOptions) -> None:
        """バックグラウンドスレッド。進捗は progress コールバック→キュー経由で流す。"""
        started_at = datetime.now()
        delim_disp = repr(options.delimiter) if options.delimiter else "自動検出"

        header = (
            "━" * 50 + "\n"
            f"  開始時刻  : {started_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  ファイル  : {input_path}\n"
            f"  分割行数  : {options.rows_per_file:,} 行\n"
            f"  エンコード: {options.encoding}\n"
            f"  デリミタ  : {delim_disp}\n"
            f"  ヘッダー  : {'あり' if options.has_header else 'なし'}\n"
            "━" * 50 + "\n"
        )
        self._log_queue.put(header)

        error_msg = ""
        result = None
        try:
            result = split_csv(
                input_path,
                options,
                progress=lambda msg: self._log_queue.put(msg + "\n"),
            )
        except Exception as e:
            error_msg = str(e)
            self._log_queue.put(f"[ERROR] {e}\n")
        finally:
            ended_at = datetime.now()
            elapsed = ended_at - started_at
            total_sec = int(elapsed.total_seconds())
            elapsed_str = f"{total_sec // 60}分{total_sec % 60}秒" if total_sec >= 60 else f"{total_sec}秒"
            status = "ERROR" if error_msg else "SUCCESS"

            footer = (
                "━" * 50 + "\n"
                f"  終了時刻    : {ended_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  経過時間    : {elapsed_str}\n"
                f"  ステータス  : {status}\n"
            )
            if not error_msg and result is not None:
                footer += (
                    f"  総データ件数: {result.total_rows:,} 行\n"
                    f"  出力ファイル: {len(result.output_summaries)} 件\n"
                    f"  出力フォルダ: {result.output_dir}\n"
                    f"  ログファイル: {result.log_path}\n"
                )
            else:
                footer += f"  エラー      : {error_msg}\n"
            footer += "━" * 50 + "\n"

            self._log_queue.put(footer)
            self._log_queue.put(_SENTINEL_SPLIT_DONE)

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
                if item is _SENTINEL_SPLIT_DONE or item is _SENTINEL_ANALYZE_DONE:
                    self._btn_run.configure(state="normal")
                    self._btn_analyze.configure(state="normal")
                elif isinstance(item, tuple) and item and item[0] is _SENTINEL_APPLY_ANALYSIS:
                    self._apply_analysis(item[1], item[2])
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
