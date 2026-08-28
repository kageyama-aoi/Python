"""show_tree.py の Tkinter GUI。

フォルダを選んでオプションを指定し、ディレクトリツリーを生成して
「コピー」で Claude 等に貼り付けられるようにする。ツリー生成ロジックは
show_tree.build_report をそのまま使う（CLI と挙動を一致させる）。
テーマ/フォントは 32_フォルダ構造Excel出力/src/theme.py を共用する。
"""
import os
import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import theme  # noqa: E402
from theme import (  # noqa: E402
    BTN_PRIMARY,
    BTN_SECONDARY,
    HEADER_FONT,
    LOG_BG,
    LOG_FG,
    LOG_FONT,
    MUTED_FG,
)

from show_tree import DEFAULT_DEPTH, build_report  # noqa: E402


def _split_list(text):
    return [t for t in re.split(r"[,\s]+", text.strip()) if t]


class ShowTreeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("show_tree — ディレクトリツリー表示")
        self.geometry("900x640")
        self.minsize(680, 480)

        self._build_ui()
        self.style = theme.apply_theme(self)
        theme.style_titlebar(self)

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        top.columnconfigure(0, weight=1)

        ttk.Label(top, text="対象フォルダ", font=HEADER_FONT).grid(
            row=0, column=0, columnspan=2, sticky="w")
        self.root_var = tk.StringVar(value=os.getcwd())
        ttk.Entry(top, textvariable=self.root_var).grid(
            row=1, column=0, sticky="ew", pady=(4, 6))
        ttk.Button(top, text="参照...", style=BTN_SECONDARY,
                   command=self._browse).grid(row=1, column=1, padx=(6, 0))

        opt = ttk.Frame(top)
        opt.grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Label(opt, text="深さ").pack(side="left")
        self.depth_var = tk.IntVar(value=DEFAULT_DEPTH)
        ttk.Spinbox(opt, from_=1, to=20, width=4, textvariable=self.depth_var).pack(
            side="left", padx=(4, 14))
        self.hidden_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt, text="隠しファイルも表示", variable=self.hidden_var).pack(
            side="left", padx=(0, 14))
        ttk.Label(opt, text="拡張子フィルタ").pack(side="left")
        self.ext_var = tk.StringVar()
        ttk.Entry(opt, textvariable=self.ext_var, width=16).pack(side="left", padx=(4, 14))
        ttk.Label(opt, text="追加除外").pack(side="left")
        self.ignore_var = tk.StringVar()
        ttk.Entry(opt, textvariable=self.ignore_var, width=16).pack(side="left", padx=(4, 0))

        act = ttk.Frame(top)
        act.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(act, text="ツリー生成", style=BTN_PRIMARY,
                   command=self._generate).pack(side="left")
        ttk.Button(act, text="コピー", style=BTN_SECONDARY,
                   command=self._copy).pack(side="left", padx=(6, 0))
        ttk.Button(act, text="保存...", style=BTN_SECONDARY,
                   command=self._save).pack(side="left", padx=(6, 0))
        self.status = ttk.Label(act, text="", foreground=MUTED_FG)
        self.status.pack(side="left", padx=(12, 0))

        self.text = ScrolledText(self, font=LOG_FONT, background=LOG_BG,
                                 foreground=LOG_FG, insertbackground=LOG_FG)
        self.text.pack(fill="both", expand=True, padx=8, pady=8)

    def _browse(self):
        current = self.root_var.get()
        path = filedialog.askdirectory(
            initialdir=current if os.path.isdir(current) else os.path.expanduser("~"),
            parent=self)
        if path:
            self.root_var.set(path)

    def _generate(self):
        try:
            report = build_report(
                self.root_var.get().strip(),
                self.depth_var.get(),
                self.hidden_var.get(),
                _split_list(self.ext_var.get()),
                _split_list(self.ignore_var.get()),
            )
        except (ValueError, tk.TclError) as exc:
            self._set_text(f"[ERROR] {exc}")
            self.status.config(text="失敗")
            return
        self._set_text("\n".join(report))
        self.status.config(text="生成しました")

    def _set_text(self, content):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)

    def _copy(self):
        content = self.text.get("1.0", "end-1c")
        if not content:
            return
        self.clipboard_clear()
        self.clipboard_append(content)
        self.status.config(text="クリップボードにコピーしました")

    def _save(self):
        content = self.text.get("1.0", "end-1c")
        if not content:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", parent=self,
            filetypes=[("テキスト", "*.txt"), ("Markdown", "*.md"), ("すべて", "*.*")])
        if not path:
            return
        try:
            Path(path).write_text(content, encoding="utf-8")
        except OSError as exc:
            self.status.config(text=f"保存に失敗: {exc}")
            return
        self.status.config(text="保存しました")


def main():
    ShowTreeApp().mainloop()


if __name__ == "__main__":
    main()
