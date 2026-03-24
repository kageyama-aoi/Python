"""
設定編集ダイアログモジュール。
TR種別ごとのYAML設定をGUI上で編集・保存する機能を提供します。
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from config_manager import ConfigManager


def open_config_editor(parent: tk.Tk, current_mode: str):
    """
    設定編集ダイアログを開きます。

    Args:
        parent: 親ウィンドウ
        current_mode: 編集対象のTR種別キー
    """
    manager = ConfigManager()
    data, file_path = manager.load_for_edit(current_mode)

    if not data:
        messagebox.showerror("エラー", f"設定データが見つかりません。\nMode: {current_mode}")
        return

    # サブウィンドウ作成
    editor = tk.Toplevel(parent)
    editor.title(f"設定編集: {current_mode}")
    editor.geometry("600x600")

    # ファイルパス表示
    ttk.Label(editor, text=f"File: {file_path}", font=("", 8)).pack(anchor="w", padx=10, pady=5)

    # フォーム生成用エリア (スクロール付き)
    canvas = tk.Canvas(editor)
    scrollbar = ttk.Scrollbar(editor, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="top", fill="both", expand=True)
    scrollbar.place(relx=1, rely=0, relheight=1, anchor="ne")

    entries = {}
    for row, (key, value) in enumerate(data.items()):
        ttk.Label(scroll_frame, text=key, font=("", 10, "bold")).grid(
            row=row, column=0, sticky="nw", padx=10, pady=5
        )

        val_str = str(value) if value is not None else ""

        if len(val_str) > 50 or "\n" in val_str:
            txt = scrolledtext.ScrolledText(scroll_frame, height=5, width=50)
            txt.insert("1.0", val_str)
            txt.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
            entries[key] = txt
        else:
            ent = ttk.Entry(scroll_frame, width=50)
            ent.insert(0, val_str)
            ent.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
            entries[key] = ent

    # 保存ボタンエリア
    action_frame = ttk.Frame(editor, padding=10)
    action_frame.pack(side="bottom", fill="x")

    def save():
        new_values = {}
        for k, widget in entries.items():
            if isinstance(widget, ttk.Entry):
                new_values[k] = widget.get()
            else:
                new_values[k] = widget.get("1.0", "end-1c")

        try:
            manager.save_setting(current_mode, new_values)
            messagebox.showinfo("成功", "設定を保存しました。")
            editor.destroy()
        except Exception as e:
            messagebox.showerror("保存エラー", str(e))

    ttk.Button(action_frame, text="保存", command=save).pack(side="right", padx=5)
    ttk.Button(action_frame, text="キャンセル", command=editor.destroy).pack(side="right", padx=5)
