# 33_CSV検証サポート ツールランチャー GUI
# text_splitter / diff_csv を起動・監視する内蔵型ランチャー。
# Python 標準ライブラリ（Tkinter）のみで動作する。
# Optional: pip install sv-ttk → Windows 11 スタイルのテーマが有効になる

import importlib.util
import json
import os
import re
import sys
import queue
import shutil
import zipfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta
from pathlib import Path

try:
    import sv_ttk as _sv_ttk
    _SV_TTK = True
except ImportError:
    _SV_TTK = False

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"

LOG_CLEANUP_DAYS = 30
OUTPUT_CLEANUP_DAYS = 30

# フォント定義（ここで一元管理。レイアウトは各ウィジェット側）
UI_FONT_FAMILY = "Yu Gothic UI"
UI_FONT = (UI_FONT_FAMILY, 9)
UI_FONT_BOLD = (UI_FONT_FAMILY, 9, "bold")
HEADER_FONT = (UI_FONT_FAMILY, 11, "bold")   # 左ペインの見出し
RUN_FONT = (UI_FONT_FAMILY, 10, "bold")      # Run / Stop ボタン
LOG_FONT = ("Consolas", 10)                  # ログ・冒頭プレビュー
CMD_FONT = ("Consolas", 9)                   # コマンドプレビュー

# ログ行の色定義（foreground / font を指定）
_LOG_TAGS = {
    "header": {"foreground": "#4a9eff"},  # blue  : === lines
    "debug": {"foreground": "#888888"},   # gray  : --- lines
    "pass": {"foreground": "#4ec94e"},    # green : ✓ / 完了 / passed
    "fail": {"foreground": "#ff5555", "font": LOG_FONT + ("bold",)},  # red bold
    "error": {"foreground": "#ff7777"},   # pink  : Error / エラー
    "warn": {"foreground": "#ffb347"},    # orange: warnings
}

# 実行結果サマリーの状態別文字色（ログ色分けと同系。ダーク/ライト両テーマで視認可能な色のみ）
_SUMMARY_COLORS = {
    "idle": "#888888",     # 待機（グレー）
    "running": "#4a9eff",  # 実行中（青）
    "done": "#4ec94e",     # 出力あり（緑）
    "empty": "#ffb347",    # 出力なし（オレンジ）
}

_OUTPUT_EXTS = {".csv", ".tsv", ".txt", ".dat", ".log"}
_SENTINEL_RUN_DONE = object()  # ワーカー→メインスレッドへの完了通知（log_queue 経由）
_LOG_NAME_RE = re.compile(r"_\d{8}_\d{6}\.log$")
_MAX_ANALYZE_BYTES = 50 * 1024 * 1024  # 件数解析はこのサイズまで


# ------------------------------------------------------------------
# 汎用ヘルパー
# ------------------------------------------------------------------

def _format_filesize(size_bytes):
    """バイト数を人が読みやすいサイズ文字列に変換する。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


def _analyze_output_file(path):
    """出力ファイルを解析し (件数表示, エンコード表示) を返す。"""
    try:
        size = path.stat().st_size
        if size == 0:
            return "0 行", "(空)"
        if size > _MAX_ANALYZE_BYTES:
            return "-", "(解析スキップ)"
        raw = path.read_bytes()
        has_bom = raw.startswith(b"\xef\xbb\xbf")
        for enc, label in (("utf-8-sig", "UTF-8(BOM)" if has_bom else "UTF-8"),
                           ("cp932", "Shift-JIS")):
            try:
                text = raw.decode(enc)
                count = sum(1 for line in text.splitlines() if line.strip())
                return f"{count} 行", label
            except (UnicodeDecodeError, LookupError):
                continue
        count = sum(1 for line in raw.split(b"\n") if line.strip())
        return f"{count} 行", "不明"
    except Exception:
        return "-", "error"


def cleanup_old_logs():
    """logs/ 内の <name>_YYYYMMDD_HHMMSS.log のうち古いものを zip 化して削除する。"""
    if not LOGS_DIR.is_dir():
        return
    archive_dir = LOGS_DIR / "archive"
    cutoff = datetime.now() - timedelta(days=LOG_CLEANUP_DAYS)
    for log_file in LOGS_DIR.glob("*.log"):
        if not _LOG_NAME_RE.search(log_file.name):
            continue
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime >= cutoff:
                continue
            archive_dir.mkdir(exist_ok=True)
            zip_path = archive_dir / f"{log_file.name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(log_file, arcname=log_file.name)
            log_file.unlink()
        except OSError:
            continue


def _latest_mtime(path):
    """ファイルまたはディレクトリの最終更新日時を返す。
    ディレクトリは配下ファイルの最新 mtime を採用する（作成が古くても中身が新しければ残す）。"""
    try:
        mtime = path.stat().st_mtime
        if path.is_dir():
            for p in path.rglob("*"):
                try:
                    mtime = max(mtime, p.stat().st_mtime)
                except OSError:
                    pass
        return datetime.fromtimestamp(mtime)
    except OSError:
        return None


def _zip_and_remove(target, archive_dir):
    """ファイルまたはディレクトリを archive_dir 内に zip 化してから削除する。"""
    archive_dir.mkdir(exist_ok=True)
    zip_path = archive_dir / f"{target.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if target.is_dir():
            for p in sorted(target.rglob("*")):
                if p.is_file():
                    zf.write(p, arcname=str(p.relative_to(target.parent)))
        else:
            zf.write(target, arcname=target.name)
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def cleanup_old_outputs():
    """各ツールの output/ 内の古い出力ファイル・実行サブディレクトリを zip 化して削除する。
    text_splitter の実行ごとサブディレクトリはディレクトリ単位で 1 つの zip にまとめる。"""
    cutoff = datetime.now() - timedelta(days=OUTPUT_CLEANUP_DAYS)
    for cls in _PANEL_CLASSES:
        output_dir = BASE_DIR / cls.name / cls.output_subdir
        if not output_dir.is_dir():
            continue
        archive_dir = output_dir / "archive"
        for entry in output_dir.iterdir():
            if entry == archive_dir:
                continue
            if entry.is_file() and entry.suffix.lower() not in _OUTPUT_EXTS:
                continue
            mtime = _latest_mtime(entry)
            if mtime is None or mtime >= cutoff:
                continue
            try:
                _zip_and_remove(entry, archive_dir)
            except OSError:
                continue


def _startup_cleanup():
    """起動時のバックグラウンドクリーンアップ（ログ・出力ファイル）。"""
    cleanup_old_logs()
    cleanup_old_outputs()


def _read_head_lines(path, max_lines=10, max_bytes=64 * 1024):
    """入力ファイルの先頭 max_lines 行を (行リスト, エンコード表示名) で返す。
    先頭 max_bytes だけ読むため巨大ファイルでも高速。"""
    with open(path, "rb") as f:
        raw = f.read(max_bytes)
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    for enc, label in (("utf-8-sig", "UTF-8(BOM)" if has_bom else "UTF-8"),
                       ("cp932", "Shift-JIS")):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text, label = raw.decode("utf-8", errors="replace"), "不明"
    # 末尾はバイト境界で切れている可能性があるため、最終行は捨てる（max_lines行あれば影響なし）
    lines = text.splitlines()
    if len(raw) == max_bytes and lines:
        lines = lines[:-1]
    return lines[:max_lines], label


def _open_in_explorer(path):
    """フォルダまたはファイルを既定の方法で開く。"""
    try:
        os.startfile(str(path))
    except OSError as exc:
        messagebox.showerror("エラー", f"開けませんでした:\n{path}\n\n{exc}")


def _iter_output_files(dir_path):
    """出力ディレクトリ直下と1階層下のサブディレクトリ内の出力ファイルを列挙する。
    （text_splitter は実行ごとに output/<stem>_<日時>/ サブディレクトリへ出力する）"""
    if not dir_path.is_dir():
        return
    for p in dir_path.iterdir():
        if p.is_file() and p.suffix.lower() in _OUTPUT_EXTS:
            yield p
        elif p.is_dir():
            try:
                children = list(p.iterdir())
            except OSError:
                continue
            for q in children:
                if q.is_file() and q.suffix.lower() in _OUTPUT_EXTS:
                    yield q


def _snapshot_dir(dir_path):
    """出力ディレクトリの {相対パス: mtime} スナップショットを返す。"""
    snapshot = {}
    for p in _iter_output_files(dir_path):
        try:
            snapshot[str(p.relative_to(dir_path))] = p.stat().st_mtime
        except OSError:
            pass
    return snapshot


def _detect_new_files(dir_path, snapshot):
    """スナップショット以降に作成・更新されたファイルを新しい順で返す。"""
    results = []
    for p in _iter_output_files(dir_path):
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        key = str(p.relative_to(dir_path))
        if key not in snapshot or mtime > snapshot[key] + 0.5:
            results.append((mtime, p))
    return [p for _mtime, p in sorted(results, reverse=True)]


# ------------------------------------------------------------------
# スプラッシュスクリーン
# ------------------------------------------------------------------

class SplashScreen(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        width, height = 400, 160
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="CSV/テキスト検証サポート ランチャー",
                  font=("Yu Gothic UI", 14, "bold")).pack(pady=(16, 8))
        ttk.Label(frame, text="初期化中...").pack()
        self.update_idletasks()


# ------------------------------------------------------------------
# text_splitter config.json 編集サブウィンドウ
# ------------------------------------------------------------------

_ENCODINGS = ["utf-8", "shift_jis", "cp932", "utf-8-sig"]
_DELIMITER_CHOICES = {
    "自動判定": None,
    "カンマ (,)": ",",
    "タブ (\\t)": "\t",
    "セミコロン (;)": ";",
}


class ConfigEditorWindow(tk.Toplevel):
    """text_splitter/config.json を GUI で編集する。"""

    def __init__(self, master, config_path, on_saved=None):
        super().__init__(master)
        self.config_path = config_path
        self.presets_path = config_path.parent / "presets.json"
        self.on_saved = on_saved
        self.title("config.json 設定 (text_splitter)")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("エラー", f"config.json を読み込めません:\n{exc}", parent=master)
            self.destroy()
            return

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        # ---- お気に入り（選択でフォームに反映。保存・削除もここで行う）
        preset_frame = ttk.Frame(frame)
        preset_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(preset_frame, text="お気に入り").pack(side="left")
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                         state="readonly", width=24)
        self.preset_combo.pack(side="left", padx=8)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)
        ttk.Button(preset_frame, text="保存...", width=7,
                   command=self._save_preset).pack(side="left")
        ttk.Button(preset_frame, text="削除", width=6,
                   command=self._delete_preset).pack(side="left", padx=(4, 0))
        self._presets = {}
        self._reload_presets()

        ttk.Separator(frame).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        # ---- config.json 編集フォーム
        ttk.Label(frame, text="分割単位の行数 (rows_per_file)").grid(row=2, column=0, sticky="w", pady=4)
        self.rows_var = tk.StringVar(value=str(config.get("rows_per_file", 45000)))
        ttk.Spinbox(frame, from_=1000, to=10_000_000, increment=1000,
                    textvariable=self.rows_var,
                    width=12).grid(row=2, column=1, sticky="w", padx=(12, 0), pady=4)

        ttk.Label(frame, text="エンコード (encoding)").grid(row=3, column=0, sticky="w", pady=4)
        self.enc_var = tk.StringVar(value=config.get("encoding", "utf-8"))
        ttk.Combobox(frame, values=_ENCODINGS, textvariable=self.enc_var,
                     width=12).grid(row=3, column=1, sticky="w", padx=(12, 0), pady=4)

        ttk.Label(frame, text="区切り文字 (delimiter)").grid(row=4, column=0, sticky="w", pady=4)
        self.delim_var = tk.StringVar(value=self._delim_label(config.get("delimiter")))
        ttk.Combobox(frame, values=list(_DELIMITER_CHOICES), textvariable=self.delim_var,
                     state="readonly", width=14).grid(row=4, column=1, sticky="w", padx=(12, 0), pady=4)

        self.header_var = tk.BooleanVar(value=bool(config.get("has_header", False)))
        ttk.Checkbutton(frame, text="1行目をヘッダーとして各分割ファイルに複製する (has_header)",
                        variable=self.header_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side="left")

    @staticmethod
    def _delim_label(delim_value):
        return next((label for label, val in _DELIMITER_CHOICES.items()
                     if val == delim_value), "自動判定")

    def _form_config(self):
        """フォーム内容を config dict にして返す。不正なら None（エラー表示済み）。"""
        try:
            rows = int(self.rows_var.get())
            if rows < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("エラー", "分割単位の行数は1以上の整数で指定してください。", parent=self)
            return None
        return {
            "rows_per_file": rows,
            "encoding": self.enc_var.get().strip() or "utf-8",
            "has_header": self.header_var.get(),
            "delimiter": _DELIMITER_CHOICES.get(self.delim_var.get()),
        }

    # ---- お気に入り管理

    def _reload_presets(self, select=None):
        try:
            data = json.loads(self.presets_path.read_text(encoding="utf-8"))
            self._presets = data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            self._presets = {}
        names = list(self._presets)
        self.preset_combo["values"] = names
        if select in names:
            self.preset_var.set(select)
        elif self.preset_var.get() not in names:
            self.preset_var.set("")

    def _on_preset_selected(self, _event=None):
        preset = self._presets.get(self.preset_var.get())
        if not preset:
            return
        self.rows_var.set(str(preset.get("rows_per_file", 10000)))
        self.enc_var.set(preset.get("encoding", "utf-8"))
        self.delim_var.set(self._delim_label(preset.get("delimiter")))
        self.header_var.set(bool(preset.get("has_header", False)))

    def _write_presets(self):
        try:
            self.presets_path.write_text(
                json.dumps(self._presets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return True
        except OSError as exc:
            messagebox.showerror("エラー", f"プリセットの保存に失敗しました:\n{exc}", parent=self)
            return False

    def _save_preset(self):
        config = self._form_config()
        if config is None:
            return
        name = simpledialog.askstring(
            "お気に入り保存",
            "プリセット名を入力してください\n（現在のフォーム内容を保存します）:",
            initialvalue=self.preset_var.get(), parent=self)
        if name is None:
            return
        name = name.strip()
        if not name:
            return
        if name in self._presets and not messagebox.askyesno(
                "確認", f"プリセット「{name}」は既に存在します。上書きしますか？", parent=self):
            return
        self._presets[name] = config
        if not self._write_presets():
            return
        self._reload_presets(select=name)
        if self.on_saved:
            self.on_saved()

    def _delete_preset(self):
        name = self.preset_var.get()
        if not name or name not in self._presets:
            messagebox.showinfo("情報", "削除するプリセットを選択してください。", parent=self)
            return
        if not messagebox.askyesno("確認", f"プリセット「{name}」を削除しますか？", parent=self):
            return
        self._presets.pop(name, None)
        if not self._write_presets():
            return
        self.preset_var.set("")
        self._reload_presets()
        if self.on_saved:
            self.on_saved()

    # ---- config.json 保存

    def _save(self):
        config = self._form_config()
        if config is None:
            return
        try:
            self.config_path.write_text(
                json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("エラー", f"保存に失敗しました:\n{exc}", parent=self)
            return
        if self.on_saved:
            self.on_saved()
        self.destroy()


_analyze_module = None


def _load_analyze_module():
    """text_splitter/src/analyze.py（tkinter非依存）を読み込む。推奨分割行数ロジックを共用する。"""
    global _analyze_module
    if _analyze_module is None:
        path = BASE_DIR / "text_splitter" / "src" / "analyze.py"
        spec = importlib.util.spec_from_file_location("text_splitter_analyze", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _analyze_module = module
    return _analyze_module


# ------------------------------------------------------------------
# 入力ファイル冒頭プレビューサブウィンドウ
# ------------------------------------------------------------------

class InputPreviewWindow(tk.Toplevel):
    """選択中の入力ファイルの先頭数行を表示する。has_header 判断の材料にする。"""

    def __init__(self, master, path):
        super().__init__(master)
        self.title(f"冒頭プレビュー — {path.name}")
        self.geometry("860x320")
        self.minsize(600, 220)

        try:
            lines, enc_label = _read_head_lines(path)
        except OSError as exc:
            messagebox.showerror("エラー", f"読み込めませんでした:\n{path}\n\n{exc}", parent=master)
            self.destroy()
            return

        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text=f"エンコード: {enc_label}　（先頭 {len(lines)} 行）").grid(
            row=0, column=0, sticky="w", pady=(0, 4))

        text = tk.Text(frame, font=LOG_FONT, wrap="none", height=12)
        text.grid(row=1, column=0, sticky="nsew")
        sb_y = ttk.Scrollbar(frame, command=text.yview)
        sb_y.grid(row=1, column=1, sticky="ns")
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        sb_x.grid(row=2, column=0, sticky="ew")
        text.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        for i, line in enumerate(lines, start=1):
            text.insert("end", f"{i:>3}: {line}\n")
        text.configure(state="disabled")

        self._analyze_label = ttk.Label(
            frame, text="解析中...（総行数をカウントしています）", foreground="#4a9eff")
        self._analyze_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        hint = ttk.Label(frame, foreground="#888888",
                         text="※ 1行目が列名（ヘッダー）かどうかを確認し、設定の has_header に反映してください。")
        hint.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Button(frame, text="閉じる", command=self.destroy).grid(
            row=5, column=0, columnspan=2, sticky="e", pady=(8, 0))

        threading.Thread(target=self._analyze_worker, args=(path,), daemon=True).start()

    def _analyze_worker(self, path):
        """バックグラウンドで総行数をカウントする。UI反映は after(0,...) でメインスレッドに渡す。"""
        try:
            analyze = _load_analyze_module()
            total = analyze._count_rows(path)
            suggest = analyze._suggest_rows(total)
            size = _format_filesize(path.stat().st_size)
            text = f"サイズ: {size} ／ 総行数: {total:,} 行 ／ 推奨分割行数: {suggest}"
        except Exception as exc:
            text = f"解析に失敗しました: {exc}"
        try:
            self.after(0, self._show_analysis, text)
        except (RuntimeError, tk.TclError):
            pass  # 解析中にウィンドウが閉じられた

    def _show_analysis(self, text):
        if self.winfo_exists():
            self._analyze_label.config(text=text, foreground="")


# ------------------------------------------------------------------
# 出力ファイル詳細サブウィンドウ
# ------------------------------------------------------------------

class OutputDetailWindow(tk.Toplevel):
    """今回の実行で作成・更新された出力ファイルの詳細一覧。
    行数カウント等の解析はこのウィンドウを開いたときにだけ行う。"""

    def __init__(self, master, paths, base_dir):
        super().__init__(master)
        self.title(f"出力ファイルの詳細（{len(paths)} 件）")
        self.geometry("860x420")
        self.minsize(600, 280)
        self._output_paths = {}  # Treeview item id -> Path

        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        columns = ("name", "size", "count", "encoding")
        self.tree = ttk.Treeview(frame, columns=columns)
        self.tree.heading("#0", text="No.")
        self.tree.heading("name", text="ファイル名")
        self.tree.heading("size", text="サイズ")
        self.tree.heading("count", text="件数")
        self.tree.heading("encoding", text="形式/エンコード")
        self.tree.column("#0", width=50, anchor="e", stretch=False)
        self.tree.column("name", width=440)
        self.tree.column("size", width=90, anchor="e", stretch=False)
        self.tree.column("count", width=100, anchor="e", stretch=False)
        self.tree.column("encoding", width=120, anchor="center", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", lambda _e: self._open_selected())

        btns = ttk.Frame(frame)
        btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="フォルダを開く",
                   command=lambda: _open_in_explorer(base_dir)).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="開く", command=self._open_selected).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="閉じる", command=self.destroy).pack(side="left")

        def display_name(path):
            try:
                return str(path.relative_to(base_dir))
            except ValueError:
                return path.name

        # ファイル名の昇順（大文字小文字は無視）で項番を振って表示する
        for no, path in enumerate(sorted(paths, key=lambda p: display_name(p).lower()), start=1):
            try:
                size = _format_filesize(path.stat().st_size)
            except OSError:
                size = "-"
            count, encoding = _analyze_output_file(path)
            item = self.tree.insert("", "end", text=str(no),
                                    values=(display_name(path), size, count, encoding))
            self._output_paths[item] = path

    def _open_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("情報", "開くファイルを選択してください。", parent=self)
            return
        path = self._output_paths.get(selection[0])
        if path:
            _open_in_explorer(path)


# ------------------------------------------------------------------
# ツールパネル（左ペインの下半分に差し替え表示）
# ------------------------------------------------------------------

class ToolPanelBase(ttk.Frame):
    """各ツール固有のパラメータUIと、実行コマンドの組み立てを担う。"""

    name = ""         # 内部名（ログファイル名等に使用）
    title = ""        # 一覧表示名
    description = ""  # 説明文
    input_subdir = "input"    # 入力フォルダのツール内相対パス（サブクラスで上書き可）
    output_subdir = "output"  # 出力フォルダのツール内相対パス（サブクラスで上書き可）

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

    @property
    def tool_dir(self):
        return BASE_DIR / self.name

    @property
    def input_dir(self):
        return self.tool_dir / self.input_subdir

    @property
    def output_dir(self):
        return self.tool_dir / self.output_subdir

    def build_command(self):
        """(コマンドリスト, 作業ディレクトリ) を返す。実行不可なら ValueError。"""
        raise NotImplementedError

    def run_input_label(self):
        """実行結果サマリーに表示する入力の表示名。不明なら None。"""
        return None

    def refresh(self):
        """パネル表示時・↻ボタンで呼ばれる。ファイル一覧などを再スキャンする。"""


class TextSplitterPanel(ToolPanelBase):
    name = "text_splitter"
    title = "text_splitter — 巨大区切りテキスト分割"
    description = "巨大な区切りテキスト（CSV/TSV/TXT/DAT）を指定件数ごとに分割する。入力ファイルを選んで Run。"
    input_subdir = "data/input"
    output_subdir = "data/output"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.columnconfigure(1, weight=1)

        # 1行目: 入力ファイルに対する操作（コンボ・参照・冒頭確認）をまとめる
        ttk.Label(self, text="入力ファイル").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.input_var = tk.StringVar()
        self.input_combo = ttk.Combobox(self, textvariable=self.input_var, state="readonly")
        self.input_combo.grid(row=0, column=1, sticky="ew", padx=(8, 4), pady=(0, 6))
        self.input_combo.bind("<<ComboboxSelected>>", lambda _e: self.app.update_command_preview())
        ttk.Button(self, text="参照...", width=8,
                   command=self._browse).grid(row=0, column=2, padx=(0, 4), pady=(0, 6))
        ttk.Button(self, text="冒頭を確認", width=10,
                   command=self._open_input_preview).grid(row=0, column=3, pady=(0, 6))

        # 実行設定は config.json の1本（お気に入りの適用・保存・削除は設定ダイアログ内）
        self.config_label = ttk.Label(self, text="", foreground="#888888")
        self.config_label.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 8))

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=4, sticky="ew")
        ttk.Button(btn_frame, text="設定 (config.json)",
                   command=self._open_config_editor).pack(
            side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(btn_frame, text="単体GUIを開く",
                   command=self._open_standalone_gui).pack(
            side="left", fill="x", expand=True, padx=(4, 0))

        self._browsed_path = None
        self.refresh()

    def refresh(self):
        files = []
        if self.input_dir.is_dir():
            files = sorted(p.name for p in self.input_dir.iterdir()
                           if p.is_file() and p.suffix.lower() in (".csv", ".tsv", ".txt", ".dat"))
        values = list(files)
        if self._browsed_path:
            values.append(str(self._browsed_path))
        self.input_combo["values"] = values
        if values and not self.input_var.get():
            self.input_var.set(values[0])
        self._refresh_config_label()
        self.app.update_command_preview()

    def _refresh_config_label(self):
        try:
            config = json.loads(
                (self.tool_dir / "config" / "config.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.config_label.config(text="設定: config.json を読み込めません")
            return
        delim = config.get("delimiter")
        delim_repr = "自動" if delim in (None, "") else repr(delim)
        try:
            rows_disp = f"{int(config.get('rows_per_file')):,}"
        except (TypeError, ValueError):
            rows_disp = "?"
        self.config_label.config(text=(
            f"設定: {rows_disp} 行ごと / "
            f"{config.get('encoding', '?')} / 区切り={delim_repr} / "
            f"ヘッダー複製={'あり' if config.get('has_header') else 'なし'}"))

    def _browse(self):
        path = filedialog.askopenfilename(
            initialdir=str(self.input_dir if self.input_dir.is_dir() else self.tool_dir),
            filetypes=[("区切りテキスト", "*.csv;*.tsv;*.txt;*.dat"), ("すべて", "*.*")])
        if path:
            self._browsed_path = Path(path)
            self.refresh()
            self.input_var.set(str(self._browsed_path))
            self.app.update_command_preview()

    def _open_input_preview(self):
        path = self._resolve_input_path()
        if path is None or not path.exists():
            messagebox.showerror(
                "エラー", "入力ファイルを選択してください。" if path is None
                else f"入力ファイルが見つかりません:\n{path}")
            return
        InputPreviewWindow(self.app, path)

    def _open_config_editor(self):
        # on_saved=refresh: config保存だけでなくお気に入りの保存・削除もコンボに即反映する
        ConfigEditorWindow(self.app, self.tool_dir / "config" / "config.json",
                           on_saved=self.refresh)

    def _open_standalone_gui(self):
        gui_py = self.tool_dir / "src" / "gui.py"
        subprocess.Popen([sys.executable, str(gui_py)], cwd=str(self.tool_dir),
                         creationflags=subprocess.CREATE_NEW_CONSOLE)

    def run_input_label(self):
        selected = self.input_var.get().strip()
        return Path(selected).name if selected else None

    def _resolve_input_path(self):
        selected = self.input_var.get().strip()
        if not selected:
            return None
        path = Path(selected)
        if not path.is_absolute():
            path = self.input_dir / selected
        return path

    def build_command(self):
        input_path = self._resolve_input_path()
        if input_path is None:
            raise ValueError("入力ファイルを選択してください。\n"
                             f"（{self.input_dir} にCSVを置くか、参照ボタンで指定）")
        if not input_path.exists():
            raise ValueError(f"入力ファイルが見つかりません:\n{input_path}")
        cmd = [sys.executable, "-u", str(self.tool_dir / "src" / "run.py"), str(input_path)]
        return cmd, self.tool_dir


class DiffCsvPanel(ToolPanelBase):
    name = "diff_csv"
    title = "diff_csv — 郵便番号差分比較"
    description = "新旧2つの郵便番号CSVを比較し、差分と発行情報付きCSVを出力する。"

    _FILE_RE = re.compile(r'^(OLD_FILE|NEW_FILE)\s*=\s*INPUT_DIR\s*/\s*"([^"]+)"', re.M)

    def __init__(self, master, app):
        super().__init__(master, app)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="旧ファイル").grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.old_label = ttk.Label(self, text="-")
        self.old_label.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 2))

        ttk.Label(self, text="新ファイル").grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.new_label = ttk.Label(self, text="-")
        self.new_label.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(0, 8))

        note = ttk.Label(
            self, foreground="#888888",
            text="※ 対象ファイル名は src/postcode_diff.py に定義。変更する場合はソースを編集。")
        note.grid(row=2, column=0, columnspan=2, sticky="w")

        self.refresh()

    def refresh(self):
        expected = {}
        try:
            source = (self.tool_dir / "src" / "postcode_diff.py").read_text(encoding="utf-8")
            expected = {key: name for key, name in self._FILE_RE.findall(source)}
        except OSError:
            pass
        for key, label in (("OLD_FILE", self.old_label), ("NEW_FILE", self.new_label)):
            name = expected.get(key)
            if not name:
                label.config(text="(定義を読み取れません)", foreground="#ff7777")
                continue
            exists = (self.input_dir / name).exists()
            label.config(text=f"{name}  {'✓' if exists else '✗ 見つかりません'}",
                         foreground="#4ec94e" if exists else "#ff7777")
        self.app.update_command_preview()

    def build_command(self):
        run_py = self.tool_dir / "run.py"
        if not run_py.exists():
            raise ValueError(f"エントリポイントが見つかりません:\n{run_py}")
        return [sys.executable, "-u", str(run_py)], self.tool_dir


_PANEL_CLASSES = [TextSplitterPanel, DiffCsvPanel]


# ------------------------------------------------------------------
# メインウィンドウ
# ------------------------------------------------------------------

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        splash = SplashScreen(self)

        self.title("CSV/テキスト検証サポート ランチャー")
        self.geometry("1100x680")
        self.minsize(860, 560)

        self.log_queue = queue.Queue()
        self.proc = None
        self.is_running = False
        self.current_tool_name = None

        self._build_ui()

        if _SV_TTK:
            _sv_ttk.set_theme("dark")
        self._setup_style()  # フォント統一はテーマ適用後に行う（sv_ttkの上書きを防ぐ）

        self._select_tool(0)
        self.after(100, self._drain_log_queue)
        self.after(300, lambda: threading.Thread(target=_startup_cleanup, daemon=True).start())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        splash.destroy()
        self.deiconify()

    # -------------------------------------------------- UI 構築

    def _setup_style(self):
        """フォントの一元適用。テーマ（sv_ttk）適用後に呼ぶこと。"""
        style = ttk.Style(self)
        for name in ("TLabel", "TButton", "TCheckbutton", "TRadiobutton",
                     "TEntry", "TCombobox", "TSpinbox", "Treeview"):
            style.configure(name, font=UI_FONT)
        style.configure("TLabelframe.Label", font=UI_FONT_BOLD)   # セクションタイトル
        style.configure("Treeview.Heading", font=UI_FONT_BOLD)    # 一覧のヘッダー
        style.configure("Treeview", rowheight=24)                 # 行間をゆったりに
        style.configure("Run.TButton", font=RUN_FONT)             # Run / Stop 用

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- 左ペイン
        left = ttk.Frame(paned, padding=(0, 0, 8, 0))
        paned.add(left, weight=0)

        ttk.Label(left, text="ツール", font=HEADER_FONT).pack(anchor="w")
        self.tool_list = tk.Listbox(left, height=len(_PANEL_CLASSES) + 1, exportselection=False,
                                    font=(UI_FONT_FAMILY, 10))
        for cls in _PANEL_CLASSES:
            self.tool_list.insert("end", f" {cls.title}")
        self.tool_list.pack(fill="x", pady=(4, 4))
        self.tool_list.bind("<<ListboxSelect>>", self._on_tool_selected)

        self.desc_label = ttk.Label(left, text="", wraplength=300, foreground="#888888")
        self.desc_label.pack(anchor="w", pady=(0, 8))

        panel_box = ttk.LabelFrame(left, text="実行パラメータ", padding=12)
        panel_box.pack(fill="x", pady=(0, 8))
        self.panels = {}
        for cls in _PANEL_CLASSES:
            panel = cls(panel_box, self)
            self.panels[cls.name] = panel

        run_frame = ttk.Frame(left)
        run_frame.pack(fill="x", pady=(4, 8))
        self.run_btn = ttk.Button(run_frame, text="▶ Run", command=self._on_run,
                                  style="Run.TButton")
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stop_btn = ttk.Button(run_frame, text="■ Stop", command=self._on_stop,
                                   state="disabled", style="Run.TButton")
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        folder_frame = ttk.Frame(left)
        folder_frame.pack(fill="x")
        ttk.Button(folder_frame, text="入力フォルダ",
                   command=lambda: _open_in_explorer(self._current_panel().input_dir)
                   ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(folder_frame, text="出力フォルダ",
                   command=lambda: _open_in_explorer(self._current_panel().output_dir)
                   ).pack(side="left", fill="x", expand=True, padx=(4, 0))
        ttk.Button(folder_frame, text="↻", width=3,
                   command=lambda: self._current_panel().refresh()).pack(side="left", padx=(8, 0))

        self.status_label = ttk.Label(left, text="待機中", foreground="#888888")
        self.status_label.pack(anchor="w", pady=(12, 0))

        # ---- 右ペイン
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        cmd_frame = ttk.Frame(right)
        cmd_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        cmd_frame.columnconfigure(1, weight=1)
        ttk.Label(cmd_frame, text="Command").grid(row=0, column=0, padx=(0, 8))
        self.cmd_var = tk.StringVar()
        ttk.Entry(cmd_frame, textvariable=self.cmd_var, state="readonly",
                  font=CMD_FONT).grid(row=0, column=1, sticky="ew")

        self.log_text = ScrolledText(right, font=LOG_FONT, state="disabled",
                                     background="#1e1e1e", foreground="#e0e0e0",
                                     insertbackground="#e0e0e0")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        for tag, opts in _LOG_TAGS.items():
            self.log_text.tag_configure(tag, **opts)

        log_menu = tk.Menu(self, tearoff=0)
        log_menu.add_command(label="Save Log...", command=self._save_log_as)
        log_menu.add_command(label="Clear Log", command=self._clear_log)
        self.log_text.bind("<Button-3>", lambda e: log_menu.tk_popup(e.x_root, e.y_root))

        out_frame = ttk.LabelFrame(right, text="実行結果（今回の実行で作成・更新）", padding=6)
        out_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        out_frame.columnconfigure(0, weight=1)

        self.summary_var = tk.StringVar(value="（まだ実行していません）")
        self.summary_label = ttk.Label(out_frame, textvariable=self.summary_var,
                                       anchor="w", justify="left", font=UI_FONT_BOLD,
                                       foreground=_SUMMARY_COLORS["idle"])
        self.summary_label.grid(row=0, column=0, sticky="ew")
        self._summary_flash_job = None  # 点滅タイマー（after id）
        self.detail_btn = ttk.Button(out_frame, text="詳細...", state="disabled",
                                     command=self._open_output_detail)
        self.detail_btn.grid(row=0, column=1, padx=(6, 0))
        ttk.Button(out_frame, text="フォルダを開く",
                   command=lambda: _open_in_explorer(self._current_panel().output_dir)
                   ).grid(row=0, column=2, padx=(6, 0))

        self._last_run_files = []      # 直近の実行で作成・更新されたファイル
        self._last_output_base = None  # そのときの出力ベースディレクトリ

    # -------------------------------------------------- ツール切替

    def _current_panel(self):
        return self.panels[self.current_tool_name]

    def _on_tool_selected(self, _event=None):
        selection = self.tool_list.curselection()
        if selection:
            self._select_tool(selection[0])

    def _select_tool(self, index):
        cls = _PANEL_CLASSES[index]
        if self.current_tool_name == cls.name:
            return
        for panel in self.panels.values():
            panel.pack_forget()
        self.current_tool_name = cls.name
        panel = self.panels[cls.name]
        panel.pack(fill="x")
        panel.refresh()
        self.desc_label.config(text=cls.description)
        self.tool_list.selection_clear(0, "end")
        self.tool_list.selection_set(index)
        self.update_command_preview()

    def update_command_preview(self):
        if self.current_tool_name is None:
            return
        try:
            cmd, _cwd = self._current_panel().build_command()
            self.cmd_var.set(subprocess.list2cmdline(cmd))
        except ValueError:
            self.cmd_var.set("(実行パラメータが不足しています)")

    # -------------------------------------------------- 実行制御

    def _on_run(self):
        if self.is_running:
            return
        panel = self._current_panel()
        try:
            cmd, cwd = panel.build_command()
        except ValueError as exc:
            messagebox.showerror("実行できません", str(exc))
            return

        self.cmd_var.set(subprocess.list2cmdline(cmd))
        self._reset_run_summary()
        snapshot = _snapshot_dir(panel.output_dir)
        input_label = panel.run_input_label()

        self._set_running(True)
        self._append_log(f"=== {panel.name} 実行開始 {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")

        threading.Thread(
            target=self._run_process,
            args=(cmd, cwd, panel.name, panel.output_dir, snapshot, input_label),
            daemon=True,
        ).start()

    def _run_process(self, cmd, cwd, tool_name, output_dir, snapshot, input_label):
        """バックグラウンドスレッド。tkinter ウィジェットは直接触らず、
        ログも完了通知もスレッドセーフな log_queue 経由でメインスレッドに渡す。"""
        exit_code = None
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            proc = subprocess.Popen(
                cmd, cwd=str(cwd),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            self.proc = proc
            for line in proc.stdout:
                self.log_queue.put(line)
            exit_code = proc.wait()
        except Exception as exc:
            self.log_queue.put(f"[launcher] 実行エラー: {exc}\n")
        finally:
            self.proc = None
            self.log_queue.put((_SENTINEL_RUN_DONE,
                                (tool_name, output_dir, snapshot, exit_code, input_label)))

    def _on_run_finished(self, tool_name, output_dir, snapshot, exit_code, input_label):
        """メインスレッドで実行される後処理。"""
        if exit_code == 0:
            self._append_log(f"=== 終了 (exit code: 0) ===\n", tag="pass")
        elif exit_code is None:
            self._append_log("=== 異常終了（プロセスを起動できませんでした） ===\n", tag="fail")
        else:
            self._append_log(f"=== 終了 (exit code: {exit_code}) ===\n", tag="fail")
        self._set_running(False)
        self._autosave_log(tool_name)
        self._show_run_summary(_detect_new_files(output_dir, snapshot), output_dir, input_label)

    def _on_stop(self):
        proc = self.proc
        if proc is not None:
            self._append_log("[launcher] Stop 要求を送信しました\n", tag="warn")
            try:
                proc.terminate()
            except OSError:
                pass
        # 終了処理（ログ保存・状態リセット）はワーカースレッドの finally 経由で行われる

    def _set_running(self, running):
        self.is_running = running
        self.run_btn.config(state="disabled" if running else "normal")
        self.stop_btn.config(state="normal" if running else "disabled")
        self.tool_list.config(state="disabled" if running else "normal")
        self.status_label.config(
            text="実行中..." if running else "待機中",
            foreground="#4a9eff" if running else "#888888")

    def _on_close(self):
        proc = self.proc
        if proc is not None:
            if not messagebox.askyesno("確認", "実行中のプロセスがあります。停止して終了しますか？"):
                return
            try:
                proc.terminate()
            except OSError:
                pass
        self.destroy()

    # -------------------------------------------------- ログ表示

    @staticmethod
    def _get_log_tag(line):
        stripped = line.lstrip()
        if stripped.startswith("==="):
            return "header"
        if stripped.startswith("---"):
            return "debug"
        lower = stripped.lower()
        if "fail" in lower or stripped.startswith("Traceback"):
            return "fail"
        if stripped.startswith(("×", "Error", "ERROR")) or "エラー" in stripped or "error:" in lower:
            return "error"
        if "warn" in lower or "警告" in stripped:
            return "warn"
        if stripped.startswith("✓") or "完了" in stripped or "passed" in lower:
            return "pass"
        return None

    def _append_log(self, text, tag=None):
        if tag is None:
            tag = self._get_log_tag(text)
        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", text, tag)
        else:
            self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _flush_log_queue(self):
        while True:
            try:
                item = self.log_queue.get_nowait()
            except queue.Empty:
                break
            if isinstance(item, tuple) and item and item[0] is _SENTINEL_RUN_DONE:
                self._on_run_finished(*item[1])
            else:
                self._append_log(item)

    def _drain_log_queue(self):
        self._flush_log_queue()
        self.after(100, self._drain_log_queue)

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _save_log_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".log", initialdir=str(LOGS_DIR),
            filetypes=[("Log", "*.log"), ("すべて", "*.*")])
        if not path:
            return
        try:
            Path(path).write_text(self.log_text.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("エラー", f"保存に失敗しました:\n{exc}")

    def _autosave_log(self, tool_name):
        content = self.log_text.get("1.0", "end-1c")
        if not content.strip():
            return
        try:
            LOGS_DIR.mkdir(exist_ok=True)
            log_path = LOGS_DIR / f"{tool_name}_{datetime.now():%Y%m%d_%H%M%S}.log"
            log_path.write_text(content, encoding="utf-8")
            self._append_log(f"[launcher] ログを保存しました: {log_path}\n", tag="debug")
        except OSError as exc:
            self._append_log(f"[launcher] ログ保存に失敗: {exc}\n", tag="error")

    # -------------------------------------------------- 実行結果サマリー

    def _reset_run_summary(self):
        self._cancel_summary_flash()
        self._last_run_files = []
        self._last_output_base = None
        self.summary_var.set("実行中...")
        self.summary_label.config(foreground=_SUMMARY_COLORS["running"])
        self.detail_btn.config(state="disabled")

    def _show_run_summary(self, paths, base_dir, input_label):
        """実行完了後のサマリー1行を表示する。ファイル解析は詳細ウィンドウ側で行う。"""
        self._last_run_files = paths
        self._last_output_base = base_dir
        if not paths:
            self.summary_var.set("新しい出力ファイルはありません")
            self.detail_btn.config(state="disabled")
            self._flash_summary(_SUMMARY_COLORS["empty"])
            return
        total_size = 0
        for path in paths:
            try:
                total_size += path.stat().st_size
            except OSError:
                pass
        # 出力先が1つのサブディレクトリに揃っていればそれも表示する
        parents = {p.parent for p in paths}
        dir_part = ""
        if len(parents) == 1:
            parent = parents.pop()
            try:
                rel = parent.relative_to(base_dir)
                dir_part = f"（{rel}/）" if str(rel) != "." else ""
            except ValueError:
                dir_part = f"（{parent.name}/）"
        output_line = f"出力 {len(paths)} ファイル / {_format_filesize(total_size)} {dir_part}"
        if input_label:
            # 入力と出力は行を分けて表示する（長いファイル名・ディレクトリ名対策）
            self.summary_var.set(f"✔ 入力 {input_label}\n   {output_line}")
        else:
            self.summary_var.set(f"✔ {output_line}")
        self.detail_btn.config(state="normal")
        self._flash_summary(_SUMMARY_COLORS["done"])
        self._append_log(f"[launcher] 出力ファイル {len(paths)} 件を検出しました\n", tag="debug")

    def _flash_summary(self, color, blinks=3, interval=180):
        """サマリー行を状態色⇔グレーで点滅させて更新に気づかせる。最後は状態色で止まる。"""
        self._cancel_summary_flash()
        total_steps = blinks * 2 - 1  # 偶数step=状態色で開始・終了する

        def step(n):
            self._summary_flash_job = None
            on = (n % 2 == 0)
            self.summary_label.config(
                foreground=color if on else _SUMMARY_COLORS["idle"])
            if n + 1 < total_steps:
                self._summary_flash_job = self.after(interval, step, n + 1)

        step(0)

    def _cancel_summary_flash(self):
        if self._summary_flash_job is not None:
            self.after_cancel(self._summary_flash_job)
            self._summary_flash_job = None

    def _open_output_detail(self):
        if self._last_run_files:
            OutputDetailWindow(self, self._last_run_files, self._last_output_base)


def main():
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
