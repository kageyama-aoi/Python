# 32_フォルダ構造Excel出力 ランチャー GUI
# generate_drive_structure.py を、実行ログをリアルタイムに見ながら実行できるようにする
# 単一ツール向けランチャー。Python 標準ライブラリ（Tkinter）のみで動作する。
# 31_CSVまとめ閲覧Excel化/src/launcher_gui.py の設計を踏襲している。
# フォルダ選択ダイアログ・古い出力削除の確認ダイアログは generate_drive_structure.py 側の
# 既存のtkinterダイアログがそのまま表示される（#134でコンソール非依存のGUIダイアログ化済み）。
# Optional: pip install sv-ttk      → Windows 11 スタイルのテーマが有効になる
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

from openpyxl import load_workbook

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
CONFIG_PATH = BASE_DIR / "config" / "config.json"
OUTPUT_DIR = BASE_DIR / "data" / "output"
LOGS_DIR = BASE_DIR / "data" / "logs"
LOG_CLEANUP_DAYS = 30

ABOUT_TEXT = (
    "準備するもの： 「設定を編集...」でスキャン対象・出力設定・除外条件を確認する\n"
    "　　　　　　（実行時にフォルダ選択ダイアログが開くので、都度スキャン対象を選べる）\n"
    "出力されるもの： data/output/ に drive_structure_<日時>.xlsx（階層構造付きExcel）"
)

UI_FONT_FAMILY = "Yu Gothic UI"
UI_FONT = (UI_FONT_FAMILY, 9)
UI_FONT_BOLD = (UI_FONT_FAMILY, 9, "bold")
HEADER_FONT = (UI_FONT_FAMILY, 11, "bold")
LOG_FONT = ("ＭＳ ゴシック", 10)

# Treeview選択行の強調色（sv_ttkダークテーマの既定は低コントラストなため明示指定。31番と同じ値）
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

_SENTINEL_RUN_DONE = object()


# ------------------------------------------------------------------
# 汎用ヘルパー
# ------------------------------------------------------------------

def _format_filesize(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


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
    """data/logs/ 内の script_YYYYMMDD.log のうち古いものを zip 化して削除する。"""
    if not LOGS_DIR.is_dir():
        return
    archive_dir = LOGS_DIR / "archive"
    cutoff = datetime.now() - timedelta(days=LOG_CLEANUP_DAYS)
    for log_file in LOGS_DIR.glob("script_*.log"):
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


def load_config():
    """config/config.json を読み込む。存在しない・壊れている場合は None。"""
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _snapshot_output_dir():
    """data/output/ の {ファイル名: mtime} スナップショットを返す。"""
    snapshot = {}
    if OUTPUT_DIR.is_dir():
        for p in OUTPUT_DIR.iterdir():
            if p.is_file() and p.suffix.lower() == ".xlsx":
                try:
                    snapshot[p.name] = p.stat().st_mtime
                except OSError:
                    pass
    return snapshot


def _detect_new_output_files(snapshot):
    """スナップショット以降に作成・更新されたxlsxを新しい順で返す。"""
    if not OUTPUT_DIR.is_dir():
        return []
    results = []
    for p in OUTPUT_DIR.iterdir():
        if not (p.is_file() and p.suffix.lower() == ".xlsx"):
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if p.name not in snapshot or mtime > snapshot[p.name] + 0.5:
            results.append((mtime, p))
    return [p for _mtime, p in sorted(results, reverse=True)]


def _count_output_rows(path):
    """生成されたExcelの行数（ヘッダー除く）を返す。読めなければ None。"""
    try:
        wb = load_workbook(path, read_only=True)
        try:
            ws = wb.active
            return max(0, (ws.max_row or 1) - 1)
        finally:
            wb.close()
    except Exception:
        return None


# ------------------------------------------------------------------
# 設定編集サブウィンドウ
# ------------------------------------------------------------------

class ConfigEditorWindow(tk.Toplevel):
    """config/config.json をGUIで編集する。"""

    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.on_saved = on_saved
        self.title("設定編集 (config/config.json)")
        self.geometry("640x420")
        self.minsize(560, 380)
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()
        _style_titlebar(self)

        config = load_config()
        if config is None:
            messagebox.showerror(
                "エラー",
                f"設定ファイルを読み込めません:\n{CONFIG_PATH}\n\n"
                f"config/config.example.json をコピーして config/config.json を作成してください。",
                parent=master)
            self.destroy()
            return

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="スキャン対象フォルダ (root_dir)").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.root_dir_var = tk.StringVar(value=config.get("root_dir", ""))
        root_dir_frame = ttk.Frame(frame)
        root_dir_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        root_dir_frame.columnconfigure(0, weight=1)
        ttk.Entry(root_dir_frame, textvariable=self.root_dir_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(root_dir_frame, text="参照...", width=8, style=BTN_SECONDARY,
                   command=self._browse_root_dir).grid(row=0, column=1, padx=(6, 0))
        hint = ttk.Label(frame, foreground="#888888",
                         text="※ 実行のたびにフォルダ選択ダイアログが開くため、通常はここを編集する必要はない")
        hint.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(frame, text="出力先フォルダ (output_base_dir)").grid(row=3, column=0, sticky="w", pady=4)
        self.output_base_dir_var = tk.StringVar(value=config.get("output_base_dir", "data/output"))
        ttk.Entry(frame, textvariable=self.output_base_dir_var).grid(
            row=3, column=1, sticky="ew", padx=(12, 0), pady=4)

        ttk.Label(frame, text="出力ファイル名 (output_filename)").grid(row=4, column=0, sticky="w", pady=4)
        self.output_filename_var = tk.StringVar(value=config.get("output_filename", "drive_structure.xlsx"))
        ttk.Entry(frame, textvariable=self.output_filename_var).grid(
            row=4, column=1, sticky="ew", padx=(12, 0), pady=4)

        ttk.Label(frame, text="除外拡張子 (excluded_extensions)").grid(row=5, column=0, sticky="w", pady=4)
        self.excluded_extensions_var = tk.StringVar(
            value=", ".join(config.get("excluded_extensions", [])))
        ttk.Entry(frame, textvariable=self.excluded_extensions_var).grid(
            row=5, column=1, sticky="ew", padx=(12, 0), pady=4)

        ttk.Label(frame, text="除外フォルダ名 (excluded_folder_names)").grid(row=6, column=0, sticky="w", pady=4)
        self.excluded_folder_names_var = tk.StringVar(
            value=", ".join(config.get("excluded_folder_names", [])))
        ttk.Entry(frame, textvariable=self.excluded_folder_names_var).grid(
            row=6, column=1, sticky="ew", padx=(12, 0), pady=4)

        ttk.Label(frame, foreground="#888888", text="※ 拡張子・フォルダ名はカンマ区切りで入力").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(2, 0))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(btn_frame, text="保存", style=BTN_SECONDARY,
                   command=self._save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="キャンセル", style=BTN_TERTIARY,
                   command=self.destroy).pack(side="left")

    def _browse_root_dir(self):
        initial = self.root_dir_var.get()
        path = filedialog.askdirectory(
            title="スキャンするフォルダを選択してください",
            initialdir=initial if os.path.isdir(initial) else os.path.expanduser("~"),
            parent=self)
        if path:
            self.root_dir_var.set(path)

    def _save(self):
        config = load_config() or {}
        config["root_dir"] = self.root_dir_var.get().strip() or "."
        config["output_base_dir"] = self.output_base_dir_var.get().strip() or "data/output"
        config["output_filename"] = self.output_filename_var.get().strip() or "drive_structure.xlsx"
        config["excluded_extensions"] = [
            v.strip() for v in self.excluded_extensions_var.get().split(",") if v.strip()]
        config["excluded_folder_names"] = [
            v.strip() for v in self.excluded_folder_names_var.get().split(",") if v.strip()]
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(
                json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("エラー", f"保存に失敗しました:\n{exc}", parent=self)
            return
        if self.on_saved:
            self.on_saved()
        self.destroy()


# ------------------------------------------------------------------
# メインウィンドウ
# ------------------------------------------------------------------

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("フォルダ構造Excel出力 ランチャー")
        self.geometry("1000x660")
        self.minsize(780, 540)

        self.log_queue = queue.Queue()
        self.proc = None
        self.is_running = False
        self._last_output_file = None

        self._build_ui()

        if _SV_TTK:
            _sv_ttk.set_theme("dark")
        self._setup_style()

        self.refresh_config_summary()
        self.after(100, self._drain_log_queue)
        self.after(300, lambda: threading.Thread(target=cleanup_old_logs, daemon=True).start())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        _style_titlebar(self)

    # -------------------------------------------------- UI 構築

    def _setup_style(self):
        style = ttk.Style(self)
        for name in ("TLabel", "TButton", "TCheckbutton", "TEntry", "Treeview"):
            style.configure(name, font=UI_FONT)
        style.configure("TLabelframe.Label", font=UI_FONT_BOLD)
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

        ttk.Label(left, text="現在の設定", font=HEADER_FONT).pack(anchor="w")
        self.config_label = ttk.Label(left, text="", justify="left", wraplength=340)
        self.config_label.pack(anchor="w", fill="x", pady=(4, 8))

        cfg_btns = ttk.Frame(left)
        cfg_btns.pack(fill="x", pady=(0, 8))
        ttk.Button(cfg_btns, text="設定を編集...", style=BTN_SECONDARY,
                   command=self._open_config_editor).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(cfg_btns, text="↻", width=3, style=BTN_TERTIARY,
                   command=self.refresh_config_summary).pack(side="left", padx=(4, 0))

        run_frame = ttk.Frame(left)
        run_frame.pack(fill="x", pady=(4, 8))
        self.run_btn = ttk.Button(run_frame, text="▶ 実行", command=self._on_run,
                                  style=BTN_PRIMARY)
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stop_btn = ttk.Button(run_frame, text="■ Stop", command=self._on_stop,
                                   state="disabled", style=BTN_SECONDARY)
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        folder_frame = ttk.Frame(left)
        folder_frame.pack(fill="x")
        ttk.Button(folder_frame, text="出力フォルダを開く", style=BTN_SECONDARY,
                   command=lambda: (OUTPUT_DIR.mkdir(parents=True, exist_ok=True), _open_in_explorer(OUTPUT_DIR))
                   ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(folder_frame, text="ログフォルダを開く", style=BTN_SECONDARY,
                   command=lambda: (LOGS_DIR.mkdir(parents=True, exist_ok=True), _open_in_explorer(LOGS_DIR))
                   ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.status_label = ttk.Label(left, text="待機中", foreground="#888888")
        self.status_label.pack(anchor="w", pady=(12, 0))

        # ---- 右ペイン
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.log_text = ScrolledText(right, font=LOG_FONT, state="disabled",
                                     background="#1e1e1e", foreground="#e0e0e0",
                                     insertbackground="#e0e0e0")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        for tag, opts in _LOG_TAGS.items():
            self.log_text.tag_configure(tag, **opts)

        log_menu = tk.Menu(self, tearoff=0)
        log_menu.add_command(label="Save Log...", command=self._save_log_as)
        log_menu.add_command(label="Clear Log", command=self._clear_log)
        self.log_text.bind("<Button-3>", lambda e: log_menu.tk_popup(e.x_root, e.y_root))

        out_frame = ttk.LabelFrame(right, text="出力（data/output/）", padding=6)
        out_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        out_frame.columnconfigure(0, weight=1)

        self.summary_var = tk.StringVar(value="（まだ実行していません）")
        self.summary_label = ttk.Label(out_frame, textvariable=self.summary_var,
                                       anchor="w", justify="left", font=UI_FONT_BOLD,
                                       foreground=_SUMMARY_COLORS["idle"])
        self.summary_label.grid(row=0, column=0, sticky="ew")
        self._summary_flash_job = None
        self.open_btn = ttk.Button(out_frame, text="開く", state="disabled",
                                   style=BTN_SECONDARY, command=self._open_last_output)
        self.open_btn.grid(row=0, column=1, padx=(6, 0))

    # -------------------------------------------------- 設定サマリー

    def refresh_config_summary(self):
        config = load_config()
        if config is None:
            self.config_label.config(
                text=f"config/config.json が見つかりません。\n"
                     f"「設定を編集...」から作成してください。",
                foreground="#ff7777")
            return
        excluded_ext = ", ".join(config.get("excluded_extensions", [])) or "(なし)"
        excluded_dir = ", ".join(config.get("excluded_folder_names", [])) or "(なし)"
        self.config_label.config(foreground="", text=(
            f"root_dir:\n  {config.get('root_dir', '(未設定)')}\n\n"
            f"出力先:\n  {config.get('output_base_dir', '?')}/{config.get('output_filename', '?')}\n\n"
            f"除外拡張子:\n  {excluded_ext}\n\n"
            f"除外フォルダ名:\n  {excluded_dir}"
        ))

    def _open_config_editor(self):
        ConfigEditorWindow(self, on_saved=self.refresh_config_summary)

    # -------------------------------------------------- 実行制御

    def _on_run(self):
        if self.is_running:
            return
        if load_config() is None:
            messagebox.showerror(
                "実行できません",
                f"config/config.json が見つかりません。\n先に「設定を編集...」から作成してください。")
            return

        cmd = [sys.executable, "-u", str(BASE_DIR / "src" / "generate_drive_structure.py")]
        snapshot = _snapshot_output_dir()

        self._reset_run_summary()
        self._set_running(True)
        self._append_log(f"=== 実行開始 {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")
        self._append_log("[launcher] フォルダ選択ダイアログが開きます（前面に表示されない場合はタスクバーを確認）\n", tag="debug")

        threading.Thread(target=self._run_process, args=(cmd, snapshot), daemon=True).start()

    def _run_process(self, cmd, snapshot):
        """バックグラウンドスレッド。tkinter ウィジェットは直接触らず log_queue 経由で渡す。"""
        exit_code = None
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            proc = subprocess.Popen(
                cmd, cwd=str(BASE_DIR),
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
            self.log_queue.put((_SENTINEL_RUN_DONE, (exit_code, snapshot)))

    def _on_run_finished(self, exit_code, snapshot):
        if exit_code == 0:
            self._append_log("=== 終了 (exit code: 0) ===\n", tag="pass")
        elif exit_code is None:
            self._append_log("=== 異常終了（プロセスを起動できませんでした） ===\n", tag="fail")
        else:
            self._append_log(f"=== 終了 (exit code: {exit_code}) ===\n", tag="fail")
        self._set_running(False)

        new_files = _detect_new_output_files(snapshot)
        self._show_run_summary(new_files)

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
        if "critical" in lower or "traceback" in lower:
            return "fail"
        if stripped.startswith(("エラー", "Error", "ERROR")) or "エラー" in stripped or "error:" in lower:
            return "error"
        if "警告" in stripped or "warn" in lower:
            return "warn"
        if "完了" in stripped or "出力しました" in stripped:
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

    # -------------------------------------------------- 実行結果サマリー

    def _reset_run_summary(self):
        self._cancel_summary_flash()
        self._last_output_file = None
        self.summary_var.set("実行中...")
        self.summary_label.config(foreground=_SUMMARY_COLORS["running"])
        self.open_btn.config(state="disabled")

    def _show_run_summary(self, new_files):
        if not new_files:
            self.summary_var.set("新しい出力ファイルはありません（キャンセル、または対象0件）")
            self.open_btn.config(state="disabled")
            self._flash_summary(_SUMMARY_COLORS["empty"])
            return

        output_file = new_files[0]
        self._last_output_file = output_file
        try:
            size = _format_filesize(output_file.stat().st_size)
        except OSError:
            size = "?"
        row_count = _count_output_rows(output_file)
        row_part = f" / {row_count:,} 件" if row_count is not None else ""
        self.summary_var.set(f"✔ {output_file.name}{row_part} / {size}")
        self.open_btn.config(state="normal")
        self._flash_summary(_SUMMARY_COLORS["done"])
        self._append_log(f"[launcher] 出力ファイルを検出しました: {output_file.name}\n", tag="debug")

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

    def _open_last_output(self):
        if self._last_output_file is not None:
            _open_in_explorer(self._last_output_file)


def main():
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
