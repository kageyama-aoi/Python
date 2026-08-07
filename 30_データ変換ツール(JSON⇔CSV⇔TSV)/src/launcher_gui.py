# 30_データ変換ツール(JSON⇔CSV⇔TSV) ランチャー GUI
# json_to_tsv_columns / json_to_tsv_rows / csv_to_tsv / request_to_json を
# 1つのウィンドウから起動・監視できる内蔵型ランチャー。
# 33_テキスト・CSV前処理サポート/launcher_gui.py の設計（ToolPanelBase・入力プレビュー・
# リアルタイムログ・出力サマリー＋詳細ウィンドウ）を、4つの小さなツール向けに簡略化して踏襲している。
# Optional: pip install sv-ttk      → Windows 11 スタイルのダークテーマが有効になる
# Optional: pip install pywinstyles → タイトルバーもダークテーマに揃う（sv-ttk併用時）

import json
import os
import sys
import queue
import zipfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime, timedelta
from pathlib import Path

try:
    import sv_ttk as _sv_ttk
    _SV_TTK = True
except ImportError:
    _SV_TTK = False

try:
    import pywinstyles as _pywinstyles
    _PYWINSTYLES = True
except ImportError:
    _PYWINSTYLES = False

# src/ の1つ上（プロジェクトルート）を基準にする。cwdに依存しないため、
# run.batから起動しても直接 `python src/launcher_gui.py` を実行しても同じ場所を指す。
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = DATA_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
LEAF_LIKE_KEYS_CONFIG = CONFIG_DIR / "leaf_like_keys.json"

LOG_CLEANUP_DAYS = 30
OUTPUT_CLEANUP_DAYS = 30

ABOUT_TEXT = (
    "準備するもの： data/input/ フォルダに変換したいJSON/CSVを置く\n"
    "出力されるもの： data/output/ に変換結果（.tsv / .json）。ツールごとにファイル名は異なる"
)

UI_FONT_FAMILY = "Yu Gothic UI"
UI_FONT = (UI_FONT_FAMILY, 9)
UI_FONT_BOLD = (UI_FONT_FAMILY, 9, "bold")
HEADER_FONT = (UI_FONT_FAMILY, 11, "bold")
LOG_FONT = ("ＭＳ ゴシック", 10)
CMD_FONT = ("Consolas", 9)

# Treeview選択行の強調色（sv_ttkダークテーマの既定は低コントラストなため明示指定。31/32番と同じ値）
TREE_SELECT_BG = "#2f6fed"
TREE_SELECT_FG = "#ffffff"

BTN_PRIMARY = "Primary.Accent.TButton"
BTN_SECONDARY = "Secondary.TButton"
BTN_TERTIARY = "Tertiary.Toolbutton"
_BUTTON_SPECS = {
    BTN_PRIMARY:   {"font": (UI_FONT_FAMILY, 14, "bold"), "height": 40, "hpad": 20},
    BTN_SECONDARY: {"font": (UI_FONT_FAMILY, 11),         "height": 32, "hpad": 12},
    BTN_TERTIARY:  {"font": (UI_FONT_FAMILY, 10),         "height": 26, "hpad": 6},
}

_LOG_TAGS = {
    "header": {"foreground": "#4a9eff"},
    "debug": {"foreground": "#888888"},
    "pass": {"foreground": "#4ec94e"},
    "fail": {"foreground": "#ff5555", "font": LOG_FONT + ("bold",)},
    "error": {"foreground": "#ff7777"},
    "warn": {"foreground": "#ffb347"},
}

_SUMMARY_COLORS = {
    "idle": "#888888",
    "running": "#4a9eff",
    "done": "#4ec94e",
    "empty": "#ffb347",
}

_OUTPUT_EXTS = {".tsv", ".json"}
_SENTINEL_RUN_DONE = object()
_MAX_ANALYZE_BYTES = 50 * 1024 * 1024

# 1回のflushで処理する行数の上限と、表示欄の保持行数の上限。大量ログでの
# 「応答なし」対策（32_フォルダ構造Excel出力での実測・launcher-gui-designスキル参照）。
MAX_LOG_LINES_PER_FLUSH = 500
MAX_LOG_DISPLAY_LINES = 5000


# ------------------------------------------------------------------
# 汎用ヘルパー
# ------------------------------------------------------------------

def _format_filesize(size_bytes):
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
        text = raw.decode("utf-8", errors="replace")
        count = sum(1 for line in text.splitlines() if line.strip())
        return f"{count} 行", "UTF-8"
    except Exception:
        return "-", "error"


def _read_head_lines(path, max_lines=10, max_bytes=64 * 1024):
    """先頭 max_lines 行を (行リスト, エンコード表示名) で返す。"""
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
    lines = text.splitlines()
    if len(raw) == max_bytes and lines:
        lines = lines[:-1]
    return lines[:max_lines], label


def _style_titlebar(window):
    if not (_SV_TTK and _PYWINSTYLES):
        return
    try:
        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:
            _pywinstyles.change_header_color(window, "#1c1c1c")
        elif version.major == 10:
            _pywinstyles.apply_style(window, "dark")
            window.wm_attributes("-alpha", 0.99)
            window.wm_attributes("-alpha", 1)
    except Exception:
        pass


def _open_in_explorer(path):
    try:
        os.startfile(str(path))
    except OSError as exc:
        messagebox.showerror("エラー", f"開けませんでした:\n{path}\n\n{exc}")


def cleanup_old_logs():
    """data/logs/ 内の run_YYYYMMDD_HHMMSS.log のうち古いものを zip 化して削除する。"""
    if not LOGS_DIR.is_dir():
        return
    archive_dir = LOGS_DIR / "archive"
    cutoff = datetime.now() - timedelta(days=LOG_CLEANUP_DAYS)
    for log_file in LOGS_DIR.glob("run_*.log"):
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


def cleanup_old_outputs():
    """data/output/ 内の古い出力ファイルをzip化して削除する。"""
    if not OUTPUT_DIR.is_dir():
        return
    archive_dir = OUTPUT_DIR / "archive"
    cutoff = datetime.now() - timedelta(days=OUTPUT_CLEANUP_DAYS)
    for entry in OUTPUT_DIR.iterdir():
        if entry == archive_dir or not entry.is_file():
            continue
        if entry.suffix.lower() not in _OUTPUT_EXTS:
            continue
        try:
            mtime = datetime.fromtimestamp(entry.stat().st_mtime)
            if mtime >= cutoff:
                continue
            archive_dir.mkdir(exist_ok=True)
            zip_path = archive_dir / f"{entry.name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(entry, arcname=entry.name)
            entry.unlink()
        except OSError:
            continue


def _startup_cleanup():
    cleanup_old_logs()
    cleanup_old_outputs()


def _snapshot_output_dir():
    snapshot = {}
    if OUTPUT_DIR.is_dir():
        for p in OUTPUT_DIR.iterdir():
            if p.is_file() and p.suffix.lower() in _OUTPUT_EXTS:
                try:
                    snapshot[p.name] = p.stat().st_mtime
                except OSError:
                    pass
    return snapshot


def _detect_new_output_files(snapshot):
    if not OUTPUT_DIR.is_dir():
        return []
    results = []
    for p in OUTPUT_DIR.iterdir():
        if not (p.is_file() and p.suffix.lower() in _OUTPUT_EXTS):
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if p.name not in snapshot or mtime > snapshot[p.name] + 0.5:
            results.append((mtime, p))
    return [p for _mtime, p in sorted(results, reverse=True)]


# ------------------------------------------------------------------
# 入力ファイル冒頭プレビューサブウィンドウ
# ------------------------------------------------------------------

class InputPreviewWindow(tk.Toplevel):
    """選択中の入力ファイルの先頭数行を表示する。"""

    def __init__(self, master, path):
        super().__init__(master)
        self.title(f"冒頭プレビュー — {path.name}")
        self.geometry("820x320")
        self.minsize(560, 220)
        _style_titlebar(self)

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

        ttk.Button(frame, text="閉じる", style=BTN_TERTIARY, command=self.destroy).grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(8, 0))


# ------------------------------------------------------------------
# leaf_like_keys 設定編集サブウィンドウ（json_to_tsv_columns専用）
# ------------------------------------------------------------------

class LeafLikeKeysEditorWindow(tk.Toplevel):
    """config/leaf_like_keys.json をGUIで編集する。"""

    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.title("設定編集 (config/leaf_like_keys.json)")
        self.geometry("560x220")
        self.resizable(True, False)
        self.transient(master)
        self.grab_set()
        _style_titlebar(self)

        try:
            data = json.loads(LEAF_LIKE_KEYS_CONFIG.read_text(encoding="utf-8"))
            keys = data.get("leaf_like_keys", [])
        except (OSError, json.JSONDecodeError):
            keys = []

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame, justify="left", wraplength=520,
            text="「JSON→TSV（横方向Level列）」で、同じ値が連続しても矢印(→)に省略しない\n"
                 "キー名（値そのものを表す項目名）を指定する。カンマ区切りで入力してください。"
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.keys_var = tk.StringVar(value=", ".join(keys))
        ttk.Entry(frame, textvariable=self.keys_var).grid(row=1, column=0, sticky="ew")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky="e", pady=(16, 0))
        ttk.Button(btn_frame, text="保存", style=BTN_SECONDARY,
                  command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="キャンセル", style=BTN_TERTIARY,
                  command=self.destroy).pack(side="left")

    def _save(self):
        keys = [v.strip() for v in self.keys_var.get().split(",") if v.strip()]
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            LEAF_LIKE_KEYS_CONFIG.write_text(
                json.dumps({"leaf_like_keys": keys}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("エラー", f"保存に失敗しました:\n{exc}", parent=self)
            return
        if self.on_saved:
            self.on_saved()
        self.destroy()


# ------------------------------------------------------------------
# 出力ファイル詳細サブウィンドウ
# ------------------------------------------------------------------

class OutputDetailWindow(tk.Toplevel):
    """今回の実行で作成された出力ファイルの詳細一覧。"""

    def __init__(self, master, paths, base_dir):
        super().__init__(master)
        self.title(f"出力ファイルの詳細（{len(paths)} 件）")
        self.geometry("760x420")
        self.minsize(560, 280)
        _style_titlebar(self)
        self._output_paths = {}

        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        columns = ("name", "size", "count")
        self.tree = ttk.Treeview(frame, columns=columns)
        self.tree.heading("#0", text="No.")
        self.tree.heading("name", text="ファイル名")
        self.tree.heading("size", text="サイズ")
        self.tree.heading("count", text="行数")
        self.tree.column("#0", width=50, anchor="e", stretch=False)
        self.tree.column("name", width=420)
        self.tree.column("size", width=90, anchor="e", stretch=False)
        self.tree.column("count", width=100, anchor="e", stretch=False)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frame, command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", lambda _e: self._open_selected())

        btns = ttk.Frame(frame)
        btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(btns, text="出力フォルダを開く", style=BTN_SECONDARY,
                  command=lambda: _open_in_explorer(base_dir)).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="開く", style=BTN_SECONDARY,
                  command=self._open_selected).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="閉じる", style=BTN_TERTIARY,
                  command=self.destroy).pack(side="left")

        for no, path in enumerate(sorted(paths, key=lambda p: p.name.lower()), start=1):
            try:
                size = _format_filesize(path.stat().st_size)
            except OSError:
                size = "-"
            count, _enc = _analyze_output_file(path)
            item = self.tree.insert("", "end", text=str(no), values=(path.name, size, count))
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
# ツールパネル
# ------------------------------------------------------------------

class ToolPanelBase(ttk.Frame):
    """各ツール固有のパラメータUIと、実行コマンドの組み立てを担う。"""

    name = ""
    title = ""
    description = ""

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

    def build_command(self):
        """(コマンドリスト, 作業ディレクトリ) を返す。実行不可なら ValueError。"""
        raise NotImplementedError

    def run_input_label(self):
        return None

    def refresh(self):
        pass


class _JsonFilePanelBase(ToolPanelBase):
    """json_to_tsv_columns / json_to_tsv_rows で共通の「JSONファイルを選ぶ」UI。"""

    script_name = ""  # サブクラスで指定

    def __init__(self, master, app):
        super().__init__(master, app)
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text="入力ファイル (JSON)").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.input_var = tk.StringVar()
        self.input_combo = ttk.Combobox(self, textvariable=self.input_var, state="readonly")
        self.input_combo.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.input_combo.bind("<<ComboboxSelected>>", lambda _e: self.app.update_command_preview())

        btn_row = ttk.Frame(self)
        btn_row.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(btn_row, text="参照...", style=BTN_SECONDARY,
                  command=self._browse).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(btn_row, text="冒頭を確認", style=BTN_SECONDARY,
                  command=self._open_input_preview).pack(side="left", fill="x", expand=True)

        self._browsed_path = None
        self.refresh()

    def refresh(self):
        files = []
        if INPUT_DIR.is_dir():
            files = sorted(p.name for p in INPUT_DIR.iterdir()
                           if p.is_file() and p.suffix.lower() == ".json")
        values = list(files)
        if self._browsed_path:
            values.append(str(self._browsed_path))
        self.input_combo["values"] = values
        if values and not self.input_var.get():
            self.input_var.set(values[0])
        self.app.update_command_preview()

    def _browse(self):
        path = filedialog.askopenfilename(
            initialdir=str(INPUT_DIR if INPUT_DIR.is_dir() else BASE_DIR),
            filetypes=[("JSON", "*.json"), ("すべて", "*.*")])
        if path:
            self._browsed_path = Path(path)
            self.refresh()
            self.input_var.set(str(self._browsed_path))
            self.app.update_command_preview()

    def _resolve_input_path(self):
        selected = self.input_var.get().strip()
        if not selected:
            return None
        path = Path(selected)
        if not path.is_absolute():
            path = INPUT_DIR / selected
        return path

    def _open_input_preview(self):
        path = self._resolve_input_path()
        if path is None or not path.exists():
            messagebox.showerror(
                "エラー", "入力ファイルを選択してください。" if path is None
                else f"入力ファイルが見つかりません:\n{path}")
            return
        InputPreviewWindow(self.app, path)

    def run_input_label(self):
        selected = self.input_var.get().strip()
        return Path(selected).name if selected else None

    def build_command(self):
        input_path = self._resolve_input_path()
        if input_path is None:
            raise ValueError("入力ファイルを選択してください。\n"
                             f"（{INPUT_DIR} にJSONを置くか、参照ボタンで指定）")
        if not input_path.exists():
            raise ValueError(f"入力ファイルが見つかりません:\n{input_path}")
        cmd = [sys.executable, "-u", str(BASE_DIR / "src" / self.script_name), str(input_path)]
        return cmd, BASE_DIR


class JsonToTsvColumnsPanel(_JsonFilePanelBase):
    name = "json_to_tsv_columns"
    title = "JSON→TSV（横方向Level列）"
    description = "階層パスを横方向のLevel列に展開する。同じ値が連続する場合は「→」で省略表示。"
    script_name = "json_to_tsv_columns.py"

    def __init__(self, master, app):
        super().__init__(master, app)
        ttk.Button(self, text="矢印省略の設定を編集...", style=BTN_SECONDARY,
                  command=self._open_config_editor).grid(
            row=3, column=0, sticky="ew", pady=(0, 0))

    def _open_config_editor(self):
        LeafLikeKeysEditorWindow(self.app, on_saved=lambda: None)


class JsonToTsvRowsPanel(_JsonFilePanelBase):
    name = "json_to_tsv_rows"
    title = "JSON→TSV（縦方向Level/Key/Value）"
    description = "階層を縦方向のLevel/Key/Value行に展開する。ネストの深さが不揃いなデータ向け。"
    script_name = "json_to_tsv_rows.py"


class CsvToTsvPanel(ToolPanelBase):
    name = "csv_to_tsv"
    title = "CSV→TSV 一括変換"
    description = "data/input/ 内の全CSVファイルを一括でTSVに変換する（UTF-8/Shift-JIS自動判定）。"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.columnconfigure(0, weight=1)
        self.count_label = ttk.Label(self, text="")
        self.count_label.grid(row=0, column=0, sticky="w")
        self.refresh()

    def refresh(self):
        count = 0
        if INPUT_DIR.is_dir():
            count = sum(1 for p in INPUT_DIR.iterdir() if p.is_file() and p.suffix.lower() == ".csv")
        self.count_label.config(
            text=f"data/input/ 内のCSVファイル: {count} 件",
            foreground="" if count else "#ffb347")
        self.app.update_command_preview()

    def build_command(self):
        cmd = [sys.executable, "-u", str(BASE_DIR / "src" / "csv_to_tsv.py")]
        return cmd, BASE_DIR


class RequestToJsonPanel(ToolPanelBase):
    name = "request_to_json"
    title = "クエリ文字列→JSON"
    description = "URLクエリ文字列（loginId=xxx&pwd=yyy形式）をJSONに変換して保存する。"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="クエリ文字列").grid(row=0, column=0, sticky="w")
        self.query_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.query_var)
        entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        entry.bind("<KeyRelease>", lambda _e: self.app.update_command_preview())

        ttk.Label(self, foreground="#888888",
                 text="例: loginId=0190019&pwd=n6hj*oA&smsgroup=teacher").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def run_input_label(self):
        return self.query_var.get().strip() or None

    def build_command(self):
        query = self.query_var.get().strip()
        if not query:
            raise ValueError("クエリ文字列を入力してください。")
        cmd = [sys.executable, "-u", str(BASE_DIR / "src" / "request_to_json.py"), query]
        return cmd, BASE_DIR


_PANEL_CLASSES = [JsonToTsvColumnsPanel, JsonToTsvRowsPanel, CsvToTsvPanel, RequestToJsonPanel]


# ------------------------------------------------------------------
# メインウィンドウ
# ------------------------------------------------------------------

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("データ変換ツール（JSON⇔CSV⇔TSV） ランチャー")
        self.geometry("1080x680")
        self.minsize(860, 560)

        self.log_queue = queue.Queue()
        self.proc = None
        self.is_running = False
        self.current_tool_name = None
        self._last_run_files = []

        self._build_ui()

        if _SV_TTK:
            _sv_ttk.set_theme("dark")
        self._setup_style()

        self._select_tool(0)
        self.after(100, self._drain_log_queue)
        self.after(300, lambda: threading.Thread(target=_startup_cleanup, daemon=True).start())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        _style_titlebar(self)

    # -------------------------------------------------- UI 構築

    def _setup_style(self):
        style = ttk.Style(self)
        for name in ("TLabel", "TButton", "TCheckbutton", "TEntry", "TCombobox", "Treeview"):
            style.configure(name, font=UI_FONT)
        style.configure("TLabelframe.Label", font=UI_FONT_BOLD)
        style.configure("Treeview.Heading", font=UI_FONT_BOLD)
        style.configure("Treeview", rowheight=24)
        style.map("Treeview", background=[("selected", TREE_SELECT_BG)],
                  foreground=[("selected", TREE_SELECT_FG)])

        for style_name, spec in _BUTTON_SPECS.items():
            style.configure(style_name, font=spec["font"], padding=(spec["hpad"], 0))
            probe = ttk.Button(self, text="あ", style=style_name)
            self.update_idletasks()
            base_h = probe.winfo_reqheight()
            probe.destroy()
            extra = max(0, spec["height"] - base_h)
            top, bottom = extra // 2, extra - extra // 2
            style.configure(style_name, padding=(spec["hpad"], top, spec["hpad"], bottom))
        style.configure(BTN_TERTIARY, foreground="#888888")

    def _build_ui(self):
        about = ttk.LabelFrame(self, text="このツールについて", padding=10)
        about.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(about, text=ABOUT_TEXT, justify="left").pack(anchor="w")

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

        self.desc_label = ttk.Label(left, text="", wraplength=320, foreground="#888888")
        self.desc_label.pack(anchor="w", pady=(0, 8))

        panel_box = ttk.LabelFrame(left, text="実行パラメータ", padding=12)
        panel_box.pack(fill="x", pady=(0, 8))
        self.panels = {}
        for cls in _PANEL_CLASSES:
            panel = cls(panel_box, self)
            self.panels[cls.name] = panel

        run_frame = ttk.Frame(left)
        run_frame.pack(fill="x", pady=(4, 8))
        self.run_btn = ttk.Button(run_frame, text="▶ Run", command=self._on_run, style=BTN_PRIMARY)
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stop_btn = ttk.Button(run_frame, text="■ Stop", command=self._on_stop,
                                   state="disabled", style=BTN_SECONDARY)
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        folder_frame = ttk.Frame(left)
        folder_frame.pack(fill="x")
        ttk.Button(folder_frame, text="入力フォルダ", style=BTN_SECONDARY,
                  command=lambda: (INPUT_DIR.mkdir(parents=True, exist_ok=True), _open_in_explorer(INPUT_DIR))
                  ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(folder_frame, text="出力フォルダ", style=BTN_SECONDARY,
                  command=lambda: (OUTPUT_DIR.mkdir(parents=True, exist_ok=True), _open_in_explorer(OUTPUT_DIR))
                  ).pack(side="left", fill="x", expand=True, padx=(4, 4))
        ttk.Button(folder_frame, text="↻", width=3, style=BTN_TERTIARY,
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

        out_frame = ttk.LabelFrame(right, text="実行結果（今回の実行で作成）", padding=6)
        out_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        out_frame.columnconfigure(0, weight=1)

        self.summary_var = tk.StringVar(value="（まだ実行していません）")
        self.summary_label = ttk.Label(out_frame, textvariable=self.summary_var,
                                       anchor="w", justify="left", font=UI_FONT_BOLD,
                                       foreground=_SUMMARY_COLORS["idle"])
        self.summary_label.grid(row=0, column=0, sticky="ew")
        self._summary_flash_job = None
        self.detail_btn = ttk.Button(out_frame, text="詳細...", state="disabled",
                                     style=BTN_SECONDARY, command=self._open_output_detail)
        self.detail_btn.grid(row=0, column=1, padx=(6, 0))

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
        snapshot = _snapshot_output_dir()
        input_label = panel.run_input_label()

        self._set_running(True)
        self._append_log(f"=== {panel.name} 実行開始 {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")

        threading.Thread(
            target=self._run_process,
            args=(cmd, cwd, panel.name, snapshot, input_label),
            daemon=True,
        ).start()

    def _run_process(self, cmd, cwd, tool_name, snapshot, input_label):
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
            self.log_queue.put((_SENTINEL_RUN_DONE, (tool_name, snapshot, exit_code, input_label)))

    def _on_run_finished(self, tool_name, snapshot, exit_code, input_label):
        if exit_code == 0:
            self._append_log("=== 終了 (exit code: 0) ===\n", tag="pass")
        elif exit_code is None:
            self._append_log("=== 異常終了（プロセスを起動できませんでした） ===\n", tag="fail")
        else:
            self._append_log(f"=== 終了 (exit code: {exit_code}) ===\n", tag="fail")
        self._set_running(False)
        new_files = _detect_new_output_files(snapshot)
        self._show_run_summary(new_files, input_label)
        if self.current_tool_name in self.panels:
            self.panels[self.current_tool_name].refresh()

    def _on_stop(self):
        proc = self.proc
        if proc is not None:
            self._append_log("[launcher] Stop 要求を送信しました\n", tag="warn")
            try:
                proc.terminate()
            except OSError:
                pass

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
        lower = stripped.lower()
        if stripped.startswith(("エラー", "Error", "ERROR")) or "エラー" in stripped or "error:" in lower:
            return "error"
        if "警告" in stripped or "warn" in lower:
            return "warn"
        if "完了" in stripped or "生成" in stripped or "変換完了" in stripped:
            return "pass"
        return None

    def _append_log(self, text, tag=None):
        """1行だけを即座に反映する（コード内から直接呼ぶ少数呼び出し用）。"""
        self._append_log_lines([(text, tag)])

    def _append_log_lines(self, entries):
        """複数行をまとめて1回のstate切替・see("end")で反映する（応答なし対策）。"""
        if not entries:
            return
        self.log_text.configure(state="normal")
        for text, tag in entries:
            if tag is None:
                tag = self._get_log_tag(text)
            if tag:
                self.log_text.insert("end", text, tag)
            else:
                self.log_text.insert("end", text)
        self._trim_log_if_needed()
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _trim_log_if_needed(self):
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > MAX_LOG_DISPLAY_LINES:
            excess = line_count - MAX_LOG_DISPLAY_LINES
            self.log_text.delete("1.0", f"{excess + 1}.0")

    def _flush_log_queue(self):
        pending = []
        processed = 0
        while processed < MAX_LOG_LINES_PER_FLUSH:
            try:
                item = self.log_queue.get_nowait()
            except queue.Empty:
                break
            processed += 1
            if isinstance(item, tuple) and item and item[0] is _SENTINEL_RUN_DONE:
                if pending:
                    self._append_log_lines(pending)
                    pending = []
                self._on_run_finished(*item[1])
            else:
                pending.append((item, None))
        if pending:
            self._append_log_lines(pending)

    def _drain_log_queue(self):
        self._flush_log_queue()
        self.after(100, self._drain_log_queue)

    # -------------------------------------------------- 実行結果サマリー

    def _reset_run_summary(self):
        self._cancel_summary_flash()
        self._last_run_files = []
        self.summary_var.set("実行中...")
        self.summary_label.config(foreground=_SUMMARY_COLORS["running"])
        self.detail_btn.config(state="disabled")

    def _show_run_summary(self, paths, input_label):
        self._last_run_files = paths
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
        output_line = f"出力 {len(paths)} ファイル / {_format_filesize(total_size)}"
        if input_label:
            self.summary_var.set(f"✔ 入力 {input_label}\n   {output_line}")
        else:
            self.summary_var.set(f"✔ {output_line}")
        self.detail_btn.config(state="normal")
        self._flash_summary(_SUMMARY_COLORS["done"])
        self._append_log(f"[launcher] 出力ファイル {len(paths)} 件を検出しました\n", tag="debug")

    def _flash_summary(self, color, blinks=3, interval=180):
        self._cancel_summary_flash()
        total_steps = blinks * 2 - 1

        def step(n):
            self._summary_flash_job = None
            on = (n % 2 == 0)
            self.summary_label.config(foreground=color if on else _SUMMARY_COLORS["idle"])
            if n + 1 < total_steps:
                self._summary_flash_job = self.after(interval, step, n + 1)

        step(0)

    def _cancel_summary_flash(self):
        if self._summary_flash_job is not None:
            self.after_cancel(self._summary_flash_job)
            self._summary_flash_job = None

    def _open_output_detail(self):
        if self._last_run_files:
            OutputDetailWindow(self, self._last_run_files, OUTPUT_DIR)


def main():
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
