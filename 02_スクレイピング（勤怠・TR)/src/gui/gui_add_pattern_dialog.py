"""
TRパターン新規追加ダイアログモジュール。
GUIからTRパターン（キー・ラベル・フィールド値）を入力し、YAMLに保存する。
"""
import tkinter as tk
from tkinter import ttk, messagebox

from config import config
from config.config_manager import ConfigManager


def open_add_pattern_dialog(parent: tk.Tk, on_saved_callback):
    """
    パターン追加ダイアログを開く。

    Args:
        parent: 親ウィンドウ
        on_saved_callback: 保存完了後に呼び出すコールバック（GUI再描画用）
    """
    masters = config.CONF.get('masters', {})
    schools_projects = masters.get('schools_projects', {})
    schools_list = list(schools_projects.keys())

    # ダイアログウィンドウ
    dialog = tk.Toplevel(parent)
    dialog.title("TRパターン 新規追加")
    dialog.geometry("480x420")
    dialog.resizable(False, False)
    dialog.grab_set()  # モーダル表示

    form_frame = ttk.Frame(dialog, padding=15)
    form_frame.pack(fill="both", expand=True)

    # --- キー ---
    ttk.Label(form_frame, text="キー（識別子）*", font=("", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
    key_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=key_var, width=30).grid(row=0, column=1, sticky="w", padx=10)
    ttk.Label(form_frame, text="半角英数字", foreground="gray").grid(row=0, column=2, sticky="w")

    # --- ラベル ---
    ttk.Label(form_frame, text="表示名（ラベル）*", font=("", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
    label_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=label_var, width=30).grid(row=1, column=1, sticky="w", padx=10)

    # --- 環境選択チェックボックス ---
    ttk.Label(form_frame, text="環境選択が必要", font=("", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
    requires_env_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(form_frame, variable=requires_env_var).grid(row=2, column=1, sticky="w", padx=10)

    ttk.Separator(form_frame, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

    # --- Schools ---
    ttk.Label(form_frame, text="Schools*", font=("", 9, "bold")).grid(row=4, column=0, sticky="w", pady=5)
    schools_var = tk.StringVar()
    schools_combo = ttk.Combobox(form_frame, textvariable=schools_var, values=schools_list,
                                  state="readonly", width=28)
    schools_combo.grid(row=4, column=1, sticky="w", padx=10)

    # --- Project（Schoolsに連動） ---
    ttk.Label(form_frame, text="Project*", font=("", 9, "bold")).grid(row=5, column=0, sticky="w", pady=5)
    project_var = tk.StringVar()
    project_combo = ttk.Combobox(form_frame, textvariable=project_var,
                                  state="disabled", width=28)
    project_combo.grid(row=5, column=1, sticky="w", padx=10)

    def on_schools_change(event=None):
        selected_school = schools_var.get()
        projects = schools_projects.get(selected_school, [])
        project_combo.configure(values=projects, state="readonly")
        project_var.set(projects[0] if projects else "")

    schools_combo.bind("<<ComboboxSelected>>", on_schools_change)

    # --- Title ---
    ttk.Label(form_frame, text="Title", font=("", 9, "bold")).grid(row=6, column=0, sticky="w", pady=5)
    title_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=title_var, width=30).grid(row=6, column=1, sticky="w", padx=10)

    # --- Comments ---
    ttk.Label(form_frame, text="Comments", font=("", 9, "bold")).grid(row=7, column=0, sticky="nw", pady=5)
    comments_text = tk.Text(form_frame, height=4, width=30)
    comments_text.grid(row=7, column=1, sticky="w", padx=10)

    # --- ボタンエリア ---
    btn_frame = ttk.Frame(dialog, padding=10)
    btn_frame.pack(side="bottom", fill="x")

    def save():
        key = key_var.get().strip()
        label = label_var.get().strip()
        schools = schools_var.get()
        project = project_var.get()

        # バリデーション
        if not key:
            messagebox.showwarning("入力エラー", "キーを入力してください。", parent=dialog)
            return
        if not key.isalnum():
            messagebox.showwarning("入力エラー", "キーは半角英数字のみ使用できます。", parent=dialog)
            return
        if not label:
            messagebox.showwarning("入力エラー", "表示名を入力してください。", parent=dialog)
            return
        if not schools:
            messagebox.showwarning("入力エラー", "Schoolsを選択してください。", parent=dialog)
            return
        if not project:
            messagebox.showwarning("入力エラー", "Projectを選択してください。", parent=dialog)
            return

        fields = {
            'Schools': schools,
            'Project': project,
            'Title': title_var.get().strip(),
            'Comments': comments_text.get("1.0", "end-1c").strip(),
        }

        try:
            manager = ConfigManager()
            manager.add_pattern(
                key=key,
                label=label,
                requires_environment=requires_env_var.get(),
                fields=fields,
            )
            messagebox.showinfo("成功", f"パターン '{label}' を追加しました。", parent=dialog)
            dialog.destroy()
            on_saved_callback()
        except ValueError as e:
            messagebox.showerror("エラー", str(e), parent=dialog)
        except Exception as e:
            messagebox.showerror("保存エラー", str(e), parent=dialog)

    ttk.Button(btn_frame, text="追加", command=save).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="キャンセル", command=dialog.destroy).pack(side="right", padx=5)
