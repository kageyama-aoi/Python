"""ファイル振り分けツールの Tkinter GUI。

フォルダ選択 -> プレビュー（ドライラン）-> 実行（ライブログ）の流れ。
振り分けの計画/実行は organizer.py、設定入出力は config_io.py に委譲する。
"""
from __future__ import annotations

import configparser
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import theme
from .config_io import DEFAULT_CONFIG_PATH, OrganizeConfig, load_config
from .organizer import (
    ACTION_MOVE,
    ACTION_RENAME,
    ACTION_SKIP,
    ExecuteResult,
    PlannedMove,
    build_plan,
    execute_plan,
)
from .settings_editor import SettingsEditor

WINDOW_TITLE = "ファイル振り分けツール"
WINDOW_GEOMETRY = "820x620"

MAX_LOG_LINES_PER_FLUSH = 500
MAX_LOG_DISPLAY_LINES = 5000

# 状態ラベルの色（状態別）
STATUS_COLORS = {
    "idle": "#9aa0a6",
    "busy": "#4a90d9",
    "ok": "#3fb950",
    "warn": "#d29922",
    "error": "#f85149",
}

_ACTION_LABEL = {
    ACTION_MOVE: "移動",
    ACTION_RENAME: "移動(改名)",
    ACTION_SKIP: "スキップ",
}

_SENTINEL_DONE = object()


class OrganizeApp:
    """振り分けツールのメインウィンドウ。"""

    def __init__(self, master: tk.Tk, config_path: Path | None = None):
        self.master = master
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

        self.config = self._load_config_or_default()
        self.plan: list[PlannedMove] | None = None
        self.is_running = False
        self.log_queue: queue.Queue = queue.Queue()
        self._flash_job: str | None = None

        master.title(WINDOW_TITLE)
        master.geometry(WINDOW_GEOMETRY)
        master.minsize(680, 480)

        theme.apply_dark_theme(master)
        self._setup_styles()
        self._build_widgets()
        theme.style_titlebar(master)

        self.folder_var.set(str(self.config.target_dir))
        self._set_status(
            "準備完了。対象フォルダを確認して［プレビュー］を押してください。", "idle"
        )
        self._drain_log_queue()

    # ------------------------------------------------------------------ setup
    def _load_config_or_default(self) -> OrganizeConfig:
        try:
            return load_config(self.config_path)
        except (OSError, configparser.Error) as e:  # 設定不備でも起動はできるようにする
            messagebox.showwarning(
                WINDOW_TITLE,
                f"config.ini を読み込めませんでした。既定値で起動します。\n{e}",
            )
            return OrganizeConfig(target_dir=Path.home() / "Downloads")

    def _setup_styles(self) -> None:
        style = ttk.Style()
        base = theme.UI_FONT_FAMILY
        style.configure("Primary.TButton", font=(base, 11, "bold"), padding=(16, 8))
        style.configure("Secondary.TButton", font=(base, 10), padding=(10, 6))
        style.configure("Tertiary.TButton", font=(base, 10), padding=(6, 4))
        style.configure("Summary.TLabel", font=(base, 10))

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self.master, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.rowconfigure(2, weight=3)
        outer.rowconfigure(4, weight=2)
        outer.columnconfigure(0, weight=1)

        # --- 対象フォルダ ---
        folder_frame = ttk.Frame(outer)
        folder_frame.grid(row=0, column=0, sticky="ew")
        folder_frame.columnconfigure(1, weight=1)
        ttk.Label(folder_frame, text="対象フォルダ").grid(row=0, column=0, padx=(0, 8))
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var)
        self.folder_entry.grid(row=0, column=1, sticky="ew")
        self.browse_btn = ttk.Button(
            folder_frame, text="参照…", style="Tertiary.TButton", command=self._browse_folder
        )
        self.browse_btn.grid(row=0, column=2, padx=(8, 0))

        # --- 操作ボタン ---
        action_frame = ttk.Frame(outer)
        action_frame.grid(row=1, column=0, sticky="ew", pady=(10, 6))
        self.preview_btn = ttk.Button(
            action_frame, text="プレビュー", style="Secondary.TButton", command=self._on_preview
        )
        self.preview_btn.pack(side=tk.LEFT)
        self.execute_btn = ttk.Button(
            action_frame,
            text="この内容で実行",
            style="Primary.TButton",
            command=self._on_execute,
            state=tk.DISABLED,
        )
        self.execute_btn.pack(side=tk.LEFT, padx=8)
        self.settings_btn = ttk.Button(
            action_frame, text="設定…", style="Secondary.TButton", command=self._open_settings
        )
        self.settings_btn.pack(side=tk.RIGHT)

        # --- プレビュー結果ツリー ---
        tree_frame = ttk.Frame(outer)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        columns = ("action", "dest", "note")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=10)
        self.tree.heading("#0", text="ファイル名")
        self.tree.heading("action", text="動作")
        self.tree.heading("dest", text="移動先フォルダ")
        self.tree.heading("note", text="備考")
        self.tree.column("#0", width=320, stretch=True)
        self.tree.column("action", width=90, anchor=tk.CENTER, stretch=False)
        self.tree.column("dest", width=180, stretch=False)
        self.tree.column("note", width=180, stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.tag_configure("rename", foreground="#d29922")
        self.tree.tag_configure("skip", foreground="#9aa0a6")
        self.tree.tag_configure("newdir", foreground="#4a90d9")

        # --- サマリー / 状態 ---
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            outer, textvariable=self.status_var, style="Summary.TLabel", anchor=tk.W
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(8, 4))

        # --- 実行ログ ---
        log_frame = ttk.Frame(outer)
        log_frame.grid(row=4, column=0, sticky="nsew")
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_header = ttk.Frame(log_frame)
        log_header.grid(row=0, column=0, sticky="ew")
        ttk.Label(log_header, text="実行ログ").pack(side=tk.LEFT)
        self.clear_log_btn = ttk.Button(
            log_header, text="ログをクリア", style="Tertiary.TButton", command=self._clear_log
        )
        self.clear_log_btn.pack(side=tk.RIGHT)
        self.log_text = tk.Text(
            log_frame, height=8, state=tk.DISABLED, wrap=tk.NONE, font=theme.MONO_FONT
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.grid(row=1, column=1, sticky="ns", pady=(4, 0))
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.tag_configure("error", foreground=STATUS_COLORS["error"])

    # --------------------------------------------------------------- actions
    def _browse_folder(self) -> None:
        initial = self.folder_var.get() or str(Path.home())
        chosen = filedialog.askdirectory(initialdir=initial, title="対象フォルダを選択")
        if chosen:
            self.folder_var.set(chosen)
            self._invalidate_plan("フォルダを変更しました。［プレビュー］を押してください。")

    def _invalidate_plan(self, message: str) -> None:
        self.plan = None
        self.execute_btn.configure(state=tk.DISABLED)
        self._set_status(message, "idle")

    def _on_preview(self) -> None:
        if self.is_running:
            return
        target = Path(self.folder_var.get().strip())
        if not target.is_dir():
            messagebox.showerror(WINDOW_TITLE, f"フォルダが見つかりません:\n{target}")
            return
        self._set_running(True)
        self._set_status("プレビュー中…", "busy")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._preview_worker, args=(target,), daemon=True).start()

    def _post(self, callback, *args) -> None:
        """ワーカースレッドからメインスレッドへ処理を渡す。

        実行中にウィンドウが破棄されると after() は TclError を投げるため握る。
        """
        try:
            self.master.after(0, callback, *args)
        except tk.TclError:
            pass

    def _preview_worker(self, target: Path) -> None:
        try:
            plan = build_plan(target, self.config)
        except OSError as e:
            self._post(self._preview_failed, str(e))
            return
        self._post(self._preview_done, plan)

    def _preview_done(self, plan: list[PlannedMove]) -> None:
        self.plan = plan
        moved = renamed = skipped = 0
        new_dirs: set[str] = set()
        for item in plan:
            name = item.source.name
            if item.action == ACTION_SKIP:
                skipped += 1
                self.tree.insert(
                    "", tk.END, text=name, values=("スキップ", "", item.reason), tags=("skip",)
                )
                continue
            dest_dir_name = item.dest_dir.name if item.dest_dir else ""
            note_parts = []
            tags = []
            if item.creates_dir:
                new_dirs.add(dest_dir_name)
                note_parts.append("新規フォルダ")
                tags.append("newdir")
            if item.action == ACTION_RENAME:
                renamed += 1
                note_parts.append(f"→ {item.dest_name}")
                tags.append("rename")
            else:
                moved += 1
                tags.append("move")
            self.tree.insert(
                "",
                tk.END,
                text=name,
                values=(_ACTION_LABEL[item.action], dest_dir_name, " / ".join(note_parts)),
                tags=tuple(tags),
            )

        self._set_running(False)
        total = moved + renamed
        if total == 0:
            self._set_status(
                f"移動対象なし（スキップ {skipped} 件）。設定を見直すか別フォルダを選んでください。",
                "warn",
            )
            self.execute_btn.configure(state=tk.DISABLED)
        else:
            self._set_status(
                f"プレビュー: 移動 {moved} / 改名 {renamed} / スキップ {skipped} / "
                f"新規フォルダ {len(new_dirs)}。内容を確認して［この内容で実行］。",
                "ok",
            )
            self.execute_btn.configure(state=tk.NORMAL)

    def _preview_failed(self, message: str) -> None:
        self._set_running(False)
        self._set_status(f"プレビュー失敗: {message}", "error")
        messagebox.showerror(WINDOW_TITLE, f"プレビューに失敗しました:\n{message}")

    def _on_execute(self) -> None:
        if self.is_running or not self.plan:
            return
        movable = [p for p in self.plan if p.action != ACTION_SKIP]
        if not movable:
            return
        if not messagebox.askyesno(
            WINDOW_TITLE,
            f"{len(movable)} 件のファイルを移動します。よろしいですか？\n"
            f"対象: {self.folder_var.get()}",
        ):
            return
        self._set_running(True)
        self._set_status("実行中…", "busy")
        plan = self.plan
        threading.Thread(target=self._execute_worker, args=(plan,), daemon=True).start()

    def _execute_worker(self, plan: list[PlannedMove]) -> None:
        def on_log(message: str, level: str) -> None:
            self.log_queue.put((message, level))

        try:
            result = execute_plan(plan, on_log=on_log)
        except OSError as e:  # execute_plan は個別失敗を内部処理するが、想定外に備える
            self.log_queue.put((f"実行中に予期しないエラー: {e}", "error"))
            result = ExecuteResult(failed=1)
        self.log_queue.put((_SENTINEL_DONE, result))

    def _execute_done(self, result: ExecuteResult) -> None:
        self.plan = None
        self._set_running(False)
        self.execute_btn.configure(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        level = "error" if result.failed else "ok"
        self._set_status(
            f"完了: 移動 {result.moved} / 改名 {result.renamed} / "
            f"スキップ {result.skipped} / 失敗 {result.failed}。"
            "再度実行するには［プレビュー］から。",
            level,
        )
        self._flash_status()

    # ------------------------------------------------------------- log queue
    def _drain_log_queue(self) -> None:
        pending: list[tuple[str, str]] = []
        done_result: ExecuteResult | None = None
        processed = 0
        while processed < MAX_LOG_LINES_PER_FLUSH:
            try:
                message, meta = self.log_queue.get_nowait()
            except queue.Empty:
                break
            processed += 1
            if message is _SENTINEL_DONE:
                done_result = meta
                break
            pending.append((message, meta))
        if pending:
            self._append_log_lines(pending)
        if done_result is not None:
            self._execute_done(done_result)
        try:
            self.master.after(100, self._drain_log_queue)
        except tk.TclError:
            pass

    def _append_log_lines(self, entries: list[tuple[str, str]]) -> None:
        self.log_text.configure(state=tk.NORMAL)
        for message, level in entries:
            tag = ("error",) if level == "error" else ()
            self.log_text.insert(tk.END, message + "\n", tag)
        self._trim_log()
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _trim_log(self) -> None:
        line_count = int(self.log_text.index("end-1c").split(".")[0])
        if line_count > MAX_LOG_DISPLAY_LINES:
            excess = line_count - MAX_LOG_DISPLAY_LINES
            self.log_text.delete("1.0", f"{excess + 1}.0")

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # --------------------------------------------------------------- settings
    def _open_settings(self) -> None:
        if self.is_running:
            return
        editor = SettingsEditor(
            self.master, self.config, self.config_path, on_save=self._on_settings_saved
        )
        editor.grab_set()

    def _on_settings_saved(self, new_config: OrganizeConfig) -> None:
        self.config = new_config
        self.folder_var.set(str(new_config.target_dir))
        self._invalidate_plan("設定を保存しました。［プレビュー］で反映を確認してください。")

    # ----------------------------------------------------------------- state
    def _set_running(self, running: bool) -> None:
        self.is_running = running
        state = tk.DISABLED if running else tk.NORMAL
        self.preview_btn.configure(state=state)
        self.browse_btn.configure(state=state)
        self.settings_btn.configure(state=state)
        if running:
            self.execute_btn.configure(state=tk.DISABLED)

    def _set_status(self, message: str, level: str) -> None:
        self.status_var.set(message)
        self.status_label.configure(foreground=STATUS_COLORS.get(level, STATUS_COLORS["idle"]))

    def _flash_status(self, count: int = 6) -> None:
        if self._flash_job is not None:
            try:
                self.master.after_cancel(self._flash_job)
            except tk.TclError:
                pass
            self._flash_job = None
        if count <= 0:
            return
        current = self.status_label.cget("foreground")
        nxt = STATUS_COLORS["idle"] if current != STATUS_COLORS["idle"] else STATUS_COLORS["ok"]
        self.status_label.configure(foreground=nxt)
        self._flash_job = self.master.after(150, self._flash_status, count - 1)


def main() -> None:
    root = tk.Tk()
    OrganizeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
