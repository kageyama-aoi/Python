# 33_CSV検証サポート ツールランチャー GUI
# csv_splitter / diff_csv を起動・監視する内蔵型ランチャー。
# Python 標準ライブラリ（Tkinter）のみで動作する。
# Optional: pip install sv-ttk → Windows 11 スタイルのテーマが有効になる

import json
import os
import re
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

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"

LOG_CLEANUP_DAYS = 30
LOG_FONT = ("Courier New", 9)

# ログ行の色定義（foreground / font を指定）
_LOG_TAGS = {
    "header": {"foreground": "#4a9eff"},  # blue  : === lines
    "debug": {"foreground": "#888888"},   # gray  : --- lines
    "pass": {"foreground": "#4ec94e"},    # green : ✓ / 完了 / passed
    "fail": {"foreground": "#ff5555", "font": LOG_FONT + ("bold",)},  # red bold
    "error": {"foreground": "#ff7777"},   # pink  : Error / エラー
    "warn": {"foreground": "#ffb347"},    # orange: warnings
}

_OUTPUT_EXTS = {".csv", ".tsv", ".txt", ".log"}
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


def _open_in_explorer(path):
    """フォルダまたはファイルを既定の方法で開く。"""
    try:
        os.startfile(str(path))
    except OSError as exc:
        messagebox.showerror("エラー", f"開けませんでした:\n{path}\n\n{exc}")


def _iter_output_files(dir_path):
    """出力ディレクトリ直下と1階層下のサブディレクトリ内の出力ファイルを列挙する。
    （csv_splitter は実行ごとに output/<stem>_<日時>/ サブディレクトリへ出力する）"""
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
        ttk.Label(frame, text="CSV検証サポート ランチャー",
                  font=("Yu Gothic UI", 14, "bold")).pack(pady=(16, 8))
        ttk.Label(frame, text="初期化中...").pack()
        self.update_idletasks()


# ------------------------------------------------------------------
# csv_splitter config.json 編集サブウィンドウ
# ------------------------------------------------------------------

_ENCODINGS = ["utf-8", "shift_jis", "cp932", "utf-8-sig"]
_DELIMITER_CHOICES = {
    "自動判定": None,
    "カンマ (,)": ",",
    "タブ (\\t)": "\t",
    "セミコロン (;)": ";",
}


class ConfigEditorWindow(tk.Toplevel):
    """csv_splitter/config.json を GUI で編集する。"""

    def __init__(self, master, config_path, on_saved=None):
        super().__init__(master)
        self.config_path = config_path
        self.on_saved = on_saved
        self.title("config.json 設定 (csv_splitter)")
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

        ttk.Label(frame, text="分割単位の行数 (rows_per_file)").grid(row=0, column=0, sticky="w", pady=4)
        self.rows_var = tk.StringVar(value=str(config.get("rows_per_file", 45000)))
        ttk.Spinbox(frame, from_=1, to=10_000_000, textvariable=self.rows_var,
                    width=12).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=4)

        ttk.Label(frame, text="エンコード (encoding)").grid(row=1, column=0, sticky="w", pady=4)
        self.enc_var = tk.StringVar(value=config.get("encoding", "utf-8"))
        ttk.Combobox(frame, values=_ENCODINGS, textvariable=self.enc_var,
                     width=12).grid(row=1, column=1, sticky="w", padx=(12, 0), pady=4)

        ttk.Label(frame, text="区切り文字 (delimiter)").grid(row=2, column=0, sticky="w", pady=4)
        current_delim = config.get("delimiter")
        delim_label = next((label for label, val in _DELIMITER_CHOICES.items()
                            if val == current_delim), "自動判定")
        self.delim_var = tk.StringVar(value=delim_label)
        ttk.Combobox(frame, values=list(_DELIMITER_CHOICES), textvariable=self.delim_var,
                     state="readonly", width=14).grid(row=2, column=1, sticky="w", padx=(12, 0), pady=4)

        self.header_var = tk.BooleanVar(value=bool(config.get("has_header", False)))
        ttk.Checkbutton(frame, text="1行目をヘッダーとして各分割ファイルに複製する (has_header)",
                        variable=self.header_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=8)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side="left")

    def _save(self):
        try:
            rows = int(self.rows_var.get())
            if rows < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("エラー", "分割単位の行数は1以上の整数で指定してください。", parent=self)
            return
        config = {
            "rows_per_file": rows,
            "encoding": self.enc_var.get().strip() or "utf-8",
            "has_header": self.header_var.get(),
            "delimiter": _DELIMITER_CHOICES.get(self.delim_var.get()),
        }
        try:
            self.config_path.write_text(
                json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("エラー", f"保存に失敗しました:\n{exc}", parent=self)
            return
        if self.on_saved:
            self.on_saved()
        self.destroy()


# ------------------------------------------------------------------
# ツールパネル（左ペインの下半分に差し替え表示）
# ------------------------------------------------------------------

class ToolPanelBase(ttk.Frame):
    """各ツール固有のパラメータUIと、実行コマンドの組み立てを担う。"""

    name = ""         # 内部名（ログファイル名等に使用）
    title = ""        # 一覧表示名
    description = ""  # 説明文

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

    @property
    def tool_dir(self):
        return BASE_DIR / self.name

    @property
    def input_dir(self):
        return self.tool_dir / "input"

    @property
    def output_dir(self):
        return self.tool_dir / "output"

    def build_command(self):
        """(コマンドリスト, 作業ディレクトリ) を返す。実行不可なら ValueError。"""
        raise NotImplementedError

    def refresh(self):
        """パネル表示時・↻ボタンで呼ばれる。ファイル一覧などを再スキャンする。"""


class CsvSplitterPanel(ToolPanelBase):
    name = "csv_splitter"
    title = "csv_splitter — 巨大CSV分割"
    description = "巨大CSV/TSVを指定件数ごとに分割する。入力ファイルを選んで Run。"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="入力ファイル").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.input_var = tk.StringVar()
        self.input_combo = ttk.Combobox(self, textvariable=self.input_var, state="readonly")
        self.input_combo.grid(row=0, column=1, sticky="ew", padx=(8, 4), pady=(0, 4))
        self.input_combo.bind("<<ComboboxSelected>>", lambda _e: self.app.update_command_preview())
        ttk.Button(self, text="参照...", width=7,
                   command=self._browse).grid(row=0, column=2, pady=(0, 4))

        self.config_label = ttk.Label(self, text="", foreground="#888888")
        self.config_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 8))

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Button(btn_frame, text="設定 (config.json)",
                   command=self._open_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="単体GUIを開く",
                   command=self._open_standalone_gui).pack(side="left")

        self._browsed_path = None
        self.refresh()

    def refresh(self):
        files = []
        if self.input_dir.is_dir():
            files = sorted(p.name for p in self.input_dir.iterdir()
                           if p.is_file() and p.suffix.lower() in (".csv", ".tsv", ".txt"))
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
            config = json.loads((self.tool_dir / "config.json").read_text(encoding="utf-8"))
            delim = config.get("delimiter")
            delim_repr = "自動" if delim is None else repr(delim)
            self.config_label.config(text=(
                f"設定: {config.get('rows_per_file', '?'):,} 行ごと / "
                f"{config.get('encoding', '?')} / 区切り={delim_repr} / "
                f"ヘッダー複製={'あり' if config.get('has_header') else 'なし'}"))
        except (OSError, json.JSONDecodeError, ValueError):
            self.config_label.config(text="設定: config.json を読み込めません")

    def _browse(self):
        path = filedialog.askopenfilename(
            initialdir=str(self.input_dir if self.input_dir.is_dir() else self.tool_dir),
            filetypes=[("CSV/TSV/TXT", "*.csv;*.tsv;*.txt"), ("すべて", "*.*")])
        if path:
            self._browsed_path = Path(path)
            self.refresh()
            self.input_var.set(str(self._browsed_path))
            self.app.update_command_preview()

    def _open_config_editor(self):
        ConfigEditorWindow(self.app, self.tool_dir / "config.json",
                           on_saved=self._refresh_config_label)

    def _open_standalone_gui(self):
        gui_py = self.tool_dir / "src" / "gui.py"
        subprocess.Popen([sys.executable, str(gui_py)], cwd=str(self.tool_dir),
                         creationflags=subprocess.CREATE_NEW_CONSOLE)

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


_PANEL_CLASSES = [CsvSplitterPanel, DiffCsvPanel]


# ------------------------------------------------------------------
# メインウィンドウ
# ------------------------------------------------------------------

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        splash = SplashScreen(self)

        self.title("CSV検証サポート ランチャー")
        self.geometry("1100x680")
        self.minsize(860, 560)

        self.log_queue = queue.Queue()
        self.proc = None
        self.is_running = False
        self.current_tool_name = None

        self._build_ui()

        if _SV_TTK:
            _sv_ttk.set_theme("dark")

        self._select_tool(0)
        self.after(100, self._drain_log_queue)
        self.after(300, lambda: threading.Thread(target=cleanup_old_logs, daemon=True).start())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        splash.destroy()
        self.deiconify()

    # -------------------------------------------------- UI 構築

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # ---- 左ペイン
        left = ttk.Frame(paned, padding=(0, 0, 8, 0))
        paned.add(left, weight=0)

        ttk.Label(left, text="ツール", font=("Yu Gothic UI", 10, "bold")).pack(anchor="w")
        self.tool_list = tk.Listbox(left, height=len(_PANEL_CLASSES) + 1, exportselection=False)
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
        self.run_btn = ttk.Button(run_frame, text="▶ Run", command=self._on_run)
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stop_btn = ttk.Button(run_frame, text="■ Stop", command=self._on_stop, state="disabled")
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
        right.rowconfigure(1, weight=3)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        cmd_frame = ttk.Frame(right)
        cmd_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        cmd_frame.columnconfigure(1, weight=1)
        ttk.Label(cmd_frame, text="Command").grid(row=0, column=0, padx=(0, 8))
        self.cmd_var = tk.StringVar()
        ttk.Entry(cmd_frame, textvariable=self.cmd_var, state="readonly").grid(
            row=0, column=1, sticky="ew")

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

        out_frame = ttk.LabelFrame(right, text="出力ファイル（今回の実行で作成・更新）", padding=6)
        out_frame.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        out_frame.rowconfigure(0, weight=1)
        out_frame.columnconfigure(0, weight=1)

        columns = ("size", "count", "encoding")
        self.out_tree = ttk.Treeview(out_frame, columns=columns, height=4)
        self.out_tree.heading("#0", text="ファイル名")
        self.out_tree.heading("size", text="サイズ")
        self.out_tree.heading("count", text="件数")
        self.out_tree.heading("encoding", text="形式/エンコード")
        self.out_tree.column("#0", width=320)
        self.out_tree.column("size", width=90, anchor="e")
        self.out_tree.column("count", width=100, anchor="e")
        self.out_tree.column("encoding", width=110, anchor="center")
        self.out_tree.grid(row=0, column=0, sticky="nsew")
        self.out_tree.bind("<Double-1>", self._on_output_double_click)

        out_btns = ttk.Frame(out_frame)
        out_btns.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        ttk.Button(out_btns, text="フォルダを開く",
                   command=lambda: _open_in_explorer(self._current_panel().output_dir)
                   ).pack(fill="x", pady=(0, 4))
        ttk.Button(out_btns, text="開く", command=self._open_selected_output).pack(fill="x")

        self._output_paths = {}  # Treeview item id -> Path

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
        self._clear_output_panel()
        snapshot = _snapshot_dir(panel.output_dir)

        self._set_running(True)
        self._append_log(f"=== {panel.name} 実行開始 {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")

        threading.Thread(
            target=self._run_process,
            args=(cmd, cwd, panel.name, panel.output_dir, snapshot),
            daemon=True,
        ).start()

    def _run_process(self, cmd, cwd, tool_name, output_dir, snapshot):
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
            self.log_queue.put((_SENTINEL_RUN_DONE, (tool_name, output_dir, snapshot, exit_code)))

    def _on_run_finished(self, tool_name, output_dir, snapshot, exit_code):
        """メインスレッドで実行される後処理。"""
        if exit_code == 0:
            self._append_log(f"=== 終了 (exit code: 0) ===\n", tag="pass")
        elif exit_code is None:
            self._append_log("=== 異常終了（プロセスを起動できませんでした） ===\n", tag="fail")
        else:
            self._append_log(f"=== 終了 (exit code: {exit_code}) ===\n", tag="fail")
        self._set_running(False)
        self._autosave_log(tool_name)
        self._populate_output_panel(_detect_new_files(output_dir, snapshot), output_dir)

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

    # -------------------------------------------------- 出力ファイルパネル

    def _clear_output_panel(self):
        for item in self.out_tree.get_children():
            self.out_tree.delete(item)
        self._output_paths.clear()

    def _populate_output_panel(self, paths, base_dir):
        self._clear_output_panel()
        for path in paths:
            try:
                size = _format_filesize(path.stat().st_size)
            except OSError:
                size = "-"
            count, encoding = _analyze_output_file(path)
            try:
                display_name = str(path.relative_to(base_dir))
            except ValueError:
                display_name = path.name
            item = self.out_tree.insert("", "end", text=display_name,
                                        values=(size, count, encoding))
            self._output_paths[item] = path
        if paths:
            self._append_log(f"[launcher] 出力ファイル {len(paths)} 件を検出しました\n", tag="debug")

    def _open_selected_output(self):
        selection = self.out_tree.selection()
        if not selection:
            messagebox.showinfo("情報", "開くファイルを選択してください。")
            return
        path = self._output_paths.get(selection[0])
        if path:
            _open_in_explorer(path)

    def _on_output_double_click(self, _event):
        if self.out_tree.selection():
            self._open_selected_output()


def main():
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
