import logging
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

# src/ の1つ上（プロジェクトルート）。sys.pathへの追加とREADME.mdの場所探しの両方に使う。
# cwdに依存しないため、run.batから起動しても直接 `python src/gui.py` を実行しても同じ場所を指す。
TOOL_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(TOOL_ROOT))

from src.app_context import create_context
from src.mapping_editor_window import MappingEditorWindow
from src.utils.logger import setup_logger
from src.handlers import diff_checker, excel_to_fixed, fixed_to_excel, mapping_handler, setup_handler

# Optional: pip install sv-ttk      → Windows 11 スタイルのダークテーマが有効になる
# Optional: pip install pywinstyles → タイトルバーもダークテーマに揃う（sv-ttk併用時）
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


def _style_titlebar(window):
    """タイトルバーをダークテーマに揃える（sv_ttk＋pywinstylesがあるときだけ。失敗しても無害）。
    31/32番のlauncher_gui.pyと同じパターン。"""
    if not (_SV_TTK and _PYWINSTYLES):
        return
    try:
        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:   # Windows 11
            _pywinstyles.change_header_color(window, "#1c1c1c")
        elif version.major == 10:                            # Windows 10
            _pywinstyles.apply_style(window, "dark")
            window.wm_attributes("-alpha", 0.99)             # 色が即時反映されないための再描画ハック
            window.wm_attributes("-alpha", 1)
    except Exception:
        pass


class QueueLogHandler(logging.Handler):
    """バックグラウンドスレッドのログをqueue経由でメインスレッドへ渡す"""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        tag = getattr(record, "tag", record.levelname)
        self.log_queue.put((tag, self.format(record)))


# ログ表示欄の背景（#1e1e1e、31/32番と同じ）に対してWCAGコントラスト比4.5以上を
# 実測確認した配色（元は白背景向けの配色だったため、ダークテーマ化に伴い明るい色に調整）。
LOG_TAG_COLORS = {
    "INFO": "#e0e0e0",
    "WARNING": "#ffb347",
    "ERROR": "#ff7777",
    "START": "#4a9eff",
    "END": "#4ec94e",
    "DIFF": "#c299ff",
}

UI_FONT_FAMILY = "Yu Gothic UI"

# ボタン3段階の共通スタイル（31/32番のlauncher_gui.pyと同じ定義。この画面ではTertiaryは未使用）。
#   Primary   : 主要な変換操作（3つ）。14pt bold・高さ40px・アクセントカラー背景（sv_ttk時）
#   Secondary : 標準操作（初期セットアップ・mapping編集・フォルダを開く）。11pt・高さ32px
BTN_PRIMARY = "Primary.Accent.TButton"
BTN_SECONDARY = "Secondary.TButton"
BTN_TERTIARY = "Tertiary.Toolbutton"
_BUTTON_SPECS = {
    BTN_PRIMARY:   {"font": (UI_FONT_FAMILY, 13, "bold"), "height": 40, "hpad": 16},
    BTN_SECONDARY: {"font": (UI_FONT_FAMILY, 10),         "height": 30, "hpad": 10},
    BTN_TERTIARY:  {"font": (UI_FONT_FAMILY, 9),          "height": 24, "hpad": 6},
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

# 「このツールについて」ボタンで表示する、専門用語を避けた平易な説明。
# 詳しい仕様（設定Excelの作り方・注意点等）はREADME.mdに譲る。
ABOUT_TEXT = """このツールは、桁位置で項目が決まっている「固定長テキスト」ファイル
（1行の中で「会員番号は1〜10文字目、氏名は11〜30文字目…」のように
項目の位置があらかじめ決まっている形式）を、見やすいExcelに変換するツールです。


【できること】

・固定長テキスト → Excel 変換
  中身を、項目名の付いた見やすい表形式に変換します。
  Excel上で内容を確認したり、値を修正したりできます。

・Excel → 固定長テキスト 復元
  Excelで確認・修正した内容を、元の固定長テキストの形式に書き戻します。

・差分チェック（入力 vs 復元後）
  変換前後で値が変わっていないか、項目ごとに突き合わせて確認します。
  「特定の項目だけ直したつもりが、他が変わっていないか」のダブルチェック用です。


【はじめての場合】

1. 「環境初期化」を押す
   → サンプルファイルと、必要なフォルダ（configs/input/output等）が用意されます。

2. 「固定長テキスト → Excel 変換」を押す
   → data/input 内のファイルがExcelになって data/output に出てきます。

3. Excelで中身を確認・編集し、「Excel → 固定長テキスト 復元」で
   元の形式に戻せます。


【mapping.csv とは】

「このファイルには、この設定（項目の位置定義）を使う」という組み合わせの
一覧です。新しい種類のファイルを扱うときは「mapping.csv 更新」または
「mapping.csv 編集」で登録してください。


詳しい仕様（設定Excelの作り方、注意点など）は README.md を参照してください。
下のボタンから開けます。"""


class AboutWindow(tk.Toplevel):
    """「このツールについて」ボタンで開く、平易な説明ダイアログ。README.mdへの導線も持つ。"""

    def __init__(self, master):
        super().__init__(master)
        self.title("このツールについて")
        self.geometry("620x520")
        self.minsize(480, 360)
        self.transient(master)
        self.grab_set()
        _style_titlebar(self)

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        text = tk.Text(frame, wrap="word", font=(UI_FONT_FAMILY, 10),
                       background="#1e1e1e", foreground="#e0e0e0", padx=8, pady=8,
                       relief="flat")
        text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frame, command=text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=sb.set)
        text.insert("1.0", ABOUT_TEXT)
        text.configure(state="disabled")

        btns = ttk.Frame(frame)
        btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="README.mdを開く", style=BTN_SECONDARY,
                  command=self._open_readme).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="閉じる", style=BTN_TERTIARY,
                  command=self.destroy).pack(side="left")

    def _open_readme(self):
        readme_path = TOOL_ROOT / "README.md"
        try:
            os.startfile(str(readme_path))
        except OSError as exc:
            messagebox.showerror(
                "開けません", f"{readme_path}\n\n{exc}", parent=self,
            )


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

        if _SV_TTK:
            _sv_ttk.set_theme("dark")
        self._setup_style()  # フォント・ボタン高さの統一はテーマ適用後に行う（sv_ttkの上書きを防ぐ）

        self.after(100, self._drain_log_queue)
        _style_titlebar(self)

    def _build_logger(self):
        # CUI(src/main.py)と同じ data/logs/ にも残す（ウィンドウ表示だけだと閉じた後に追えない）
        logger = setup_logger(name="app_gui")
        handler = QueueLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
        return logger

    def _setup_style(self):
        """フォント・ボタン3段階スタイルの一元適用。テーマ（sv_ttk）適用後に呼ぶこと。
        31/32番のlauncher_gui.pyと同じpxプローブ較正パターン。"""
        style = ttk.Style(self)
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

    def _build_widgets(self):
        self.buttons = {}

        top_bar = ttk.Frame(self, padding=(10, 8, 10, 0))
        top_bar.pack(fill="x")
        ttk.Label(top_bar, text="34_Fixed2Excel", font=(UI_FONT_FAMILY, 11, "bold")).pack(side="left")
        ttk.Button(top_bar, text="このツールについて", style=BTN_TERTIARY,
                  command=self._show_about).pack(side="right")

        primary_frame = ttk.Frame(self, padding=(10, 10, 10, 4))
        primary_frame.pack(fill="x")
        for label, action_key in self.PRIMARY_ACTIONS:
            btn = ttk.Button(
                primary_frame, text=label, style=BTN_PRIMARY,
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
                setup_frame, text=label, style=BTN_SECONDARY,
                command=lambda k=action_key: self._run_action(k),
            )
            btn.pack(side="left", padx=4)
            self.buttons[action_key] = btn

        edit_mapping_btn = ttk.Button(
            setup_frame, text="mapping.csv 編集", style=BTN_SECONDARY,
            command=self._open_mapping_editor,
        )
        edit_mapping_btn.pack(side="left", padx=4)
        self.buttons["edit_mapping"] = edit_mapping_btn

        ttk.Label(self, text="フォルダを開く", padding=(10, 0)).pack(anchor="w")
        folder_frame = ttk.Frame(self, padding=(10, 2, 10, 8))
        folder_frame.pack(fill="x")
        for label, dir_key in self.FOLDER_ACTIONS:
            btn = ttk.Button(
                folder_frame, text=label, style=BTN_SECONDARY,
                command=lambda k=dir_key: self._open_folder(k),
            )
            btn.pack(side="left", padx=4)
            # 処理中でも他のファイル操作と競合しない読み取り専用操作のため、self.buttonsには入れず
            # _set_runningでの無効化対象から外す（実行中でも押せてよい）。

        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 0)).pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(
            self, state="disabled", wrap="word",
            background="#1e1e1e", foreground="#e0e0e0", insertbackground="#e0e0e0",
        )
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

    def _show_about(self):
        AboutWindow(self)

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
