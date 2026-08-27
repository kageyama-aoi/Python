"""ボタン設定フォーム（右ペイン：アクション別入力・パラメータ編集・フォーム保存）。

SettingsEditor に組み込むミックスイン。ページ編集タブ（pages_tab.py）の
リスト選択と連動してフォーム内容を切り替える。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from . import constants as C
from . import theme


class ParameterEditor(tk.Toplevel):
    """パラメータ付きURLの1パラメータ定義を編集するモーダルウィンドウ。

    保存すると self.result_param_data に parameter_definition 形式の dict が入る。
    キャンセル・未入力エラーで閉じた場合は None のまま。
    """

    def __init__(self, master, index=None, param_data=None):
        super().__init__(master)
        self.title("パラメータ編集" if index is not None else "パラメータ追加")
        theme.style_titlebar(self)
        self.transient(master)
        self.resizable(False, False)

        self.result_param_data = None
        param_data = param_data or {}

        form = ttk.Frame(self, padding=12)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="名前:").grid(row=0, column=0, sticky="w", pady=3)
        self.name_var = tk.StringVar(value=param_data.get(C.ConfigKey.NAME, ""))
        ttk.Entry(form, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(form, text="ラベル:").grid(row=1, column=0, sticky="w", pady=3)
        self.label_var = tk.StringVar(value=param_data.get(C.ConfigKey.LABEL, ""))
        ttk.Entry(form, textvariable=self.label_var, width=30).grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Label(form, text="種別:").grid(row=2, column=0, sticky="w", pady=3)
        self.type_var = tk.StringVar(value=param_data.get(C.ConfigKey.TYPE, C.ParamType.TEXT.value))
        ttk.Combobox(
            form, textvariable=self.type_var,
            values=[t.value for t in C.ParamType], state="readonly",
        ).grid(row=2, column=1, sticky="ew", pady=3)

        ttk.Label(form, text="初期値:").grid(row=3, column=0, sticky="w", pady=3)
        self.default_var = tk.StringVar(value=param_data.get(C.ConfigKey.DEFAULT_VALUE, ""))
        ttk.Entry(form, textvariable=self.default_var, width=30).grid(row=3, column=1, sticky="ew", pady=3)

        ttk.Label(form, text="選択肢(カンマ区切り):").grid(row=4, column=0, sticky="w", pady=3)
        options = param_data.get(C.ConfigKey.OPTIONS, [])
        self.options_var = tk.StringVar(value=", ".join(options))
        ttk.Entry(form, textvariable=self.options_var, width=30).grid(row=4, column=1, sticky="ew", pady=3)
        ttk.Label(
            form, text="pulldownの時のみ使用", foreground="#888888"
        ).grid(row=5, column=1, sticky="w")

        btn_row = ttk.Frame(self)
        btn_row.pack(pady=(0, 12))
        ttk.Button(btn_row, text="OK", style="Accent.TButton", command=self._on_ok).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(btn_row, text="キャンセル", command=self.destroy).pack(side="left")

        self.grab_set()

    def _on_ok(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("入力エラー", "名前は必須です。", parent=self)
            return
        param_type = self.type_var.get()
        if param_type not in (t.value for t in C.ParamType):
            messagebox.showerror(
                "入力エラー", "種別は text か pulldown を選択してください。", parent=self
            )
            return

        result = {
            C.ConfigKey.NAME: name,
            C.ConfigKey.TYPE: param_type,
            C.ConfigKey.DEFAULT_VALUE: self.default_var.get(),
        }
        label = self.label_var.get().strip()
        if label:
            result[C.ConfigKey.LABEL] = label
        options = [v.strip() for v in self.options_var.get().split(",") if v.strip()]
        if options:
            result[C.ConfigKey.OPTIONS] = options

        self.result_param_data = result
        self.destroy()


class ButtonFormMixin:
    """ボタン設定フォームの構築と保存を提供する。"""

    def create_button_form(self, parent):
        """右ペインのボタン設定フォームを構築する。"""
        self.form_entries = {}
        self._build_page_selector_maps()

        # フォームの編集状態。_form_page は編集中の内容が属するページID
        # （表示中タブに依存せず、この値へ保存する）。
        self._form_dirty = False
        self._form_page = None
        self._loaded_ref = None  # (page_name, idx) 現在フォームに読み込んでいる項目 / Noneは追加モード

        # Name
        name_label = ttk.Label(parent, text="名前:")
        name_label.pack(pady=2)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(parent, textvariable=name_var)
        name_entry.pack(fill="x", padx=5)
        self.form_entries[C.ConfigKey.NAME] = name_var

        # Action
        action_label = ttk.Label(parent, text="アクション:")
        action_label.pack(pady=2)
        action_var = tk.StringVar()
        action_combo = ttk.Combobox(parent, textvariable=action_var, values=[a.value for a in C.Action])
        action_combo.pack(fill="x", padx=5)
        action_combo.bind("<<ComboboxSelected>>", self._on_action_selected)
        self.form_entries[C.ConfigKey.ACTION] = action_var

        # --- Path/URL/Target (通常のボタン用) ---
        self.path_entry_frame = ttk.Frame(parent) # Frame to hold path/url/target widgets
        self.path_entry_frame.pack(fill="x", padx=5, pady=2)

        self.path_label = ttk.Label(self.path_entry_frame, text="パス/URL/ターゲット:")
        self.path_label.pack(pady=2)
        path_var = tk.StringVar()
        self.path_entry = ttk.Entry(self.path_entry_frame, textvariable=path_var)
        self.path_entry.pack(fill="x", padx=5)
        self.target_page_combo = ttk.Combobox(
            self.path_entry_frame,
            textvariable=path_var,
            values=list(self.page_display_to_id.keys()),
            state="readonly",
            justify="right",
        )
        self.form_entries[C.ConfigKey.PATH] = path_var # path, url, targetを同じEntryで使い回す

        # --- Parameterized URL Settings (特殊なボタン用) ---
        self.parameterized_url_frame = ttk.LabelFrame(parent, text="パラメータ設定")
        # Initially hidden

        # Base URL
        base_url_label = ttk.Label(self.parameterized_url_frame, text="ベースURL:")
        base_url_label.pack(pady=2)
        base_url_var = tk.StringVar()
        base_url_entry = ttk.Entry(self.parameterized_url_frame, textvariable=base_url_var)
        base_url_entry.pack(fill="x", padx=5)
        self.form_entries[C.ConfigKey.BASE_URL] = base_url_var

        # Parameters List
        param_list_label = ttk.Label(self.parameterized_url_frame, text="パラメータ一覧:")
        param_list_label.pack(pady=5)

        param_list_frame = ttk.Frame(self.parameterized_url_frame)
        param_list_frame.pack(fill="both", expand=True, padx=5, pady=2)

        self.parameter_listbox = tk.Listbox(param_list_frame, height=5)
        self.parameter_listbox.pack(side="left", fill="both", expand=True)
        param_scrollbar = ttk.Scrollbar(param_list_frame, orient="vertical", command=self.parameter_listbox.yview)
        param_scrollbar.pack(side="right", fill="y")
        self.parameter_listbox.config(yscrollcommand=param_scrollbar.set)

        param_buttons_frame = ttk.Frame(self.parameterized_url_frame)
        param_buttons_frame.pack(pady=5)

        add_param_button = ttk.Button(param_buttons_frame, text="パラメータ追加", command=self.add_parameter)
        add_param_button.pack(side="left", padx=2)

        edit_param_button = ttk.Button(param_buttons_frame, text="パラメータ編集", command=self.edit_parameter)
        edit_param_button.pack(side="left", padx=2)

        delete_param_button = ttk.Button(param_buttons_frame, text="パラメータ削除", command=self.delete_parameter)
        delete_param_button.pack(side="left", padx=2)

        # 保存ボタン
        save_button = ttk.Button(parent, text="フォームを保存", command=self.save_form_data)
        save_button.pack(pady=10)

        # 初期状態では通常のパス/URL/ターゲット入力が表示され、パラメータ設定は非表示
        self.on_action_change(None)

        # 入力変更を検知して未保存フラグを立てる
        for key in (C.ConfigKey.NAME, C.ConfigKey.ACTION, C.ConfigKey.PATH, C.ConfigKey.BASE_URL):
            self.form_entries[key].trace_add("write", self._mark_form_dirty)
        self._reset_form_dirty()

    # --- フォームの未保存状態の管理 --------------------------------------

    def _mark_form_dirty(self, *_args):
        self._form_dirty = True

    def _reset_form_dirty(self):
        self._form_dirty = False

    def form_has_unsaved_changes(self) -> bool:
        """フォームに未保存の変更があるか。"""
        return bool(getattr(self, "_form_dirty", False))

    def confirm_discard_form(self) -> bool:
        """未保存の変更があれば破棄してよいか確認する。続行してよければ True。"""
        if not self.form_has_unsaved_changes():
            return True
        return messagebox.askyesno(
            "未保存の変更",
            "ボタン設定フォームに未保存の変更があります。破棄して続行しますか？",
        )

    def _on_action_selected(self, event=None):
        """ユーザーがアクションを切り替えたときの処理。

        path / url / target は単一の入力欄を使い回しているため、前アクション用の
        入力値をそのまま次のアクションへ持ち越さないようクリアする。
        """
        self.form_entries[C.ConfigKey.PATH].set("")
        self.form_entries[C.ConfigKey.BASE_URL].set("")
        self.current_parameters = []
        self.update_parameter_listbox()
        self.on_action_change(event)

    def on_action_change(self, event):
        """選択アクションに応じて入力フォームを切り替える。"""
        action = self.form_entries[C.ConfigKey.ACTION].get()
        page_display_names = list(self.page_display_to_id.keys())
        if action == C.Action.OPEN_DIRECTORY:
            self.path_label.config(text="開くフォルダのパス:")
            self.path_entry.pack(fill="x", padx=5)
            self.target_page_combo.pack_forget()
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.OPEN_URL:
            self.path_label.config(text="開くWebサイトのURL:")
            self.path_entry.pack(fill="x", padx=5)
            self.target_page_combo.pack_forget()
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.SHOW_PAGE:
            self.path_label.config(text="表示するページ名:")
            self.target_page_combo.config(values=page_display_names, state="readonly")
            self.target_page_combo.pack(fill="x", padx=5)
            self.path_entry.pack_forget()
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            self.path_entry_frame.pack_forget() # Hide path entry
            self.parameterized_url_frame.pack(fill="both", expand=True, padx=5, pady=2) # Show parameterized URL frame
        else:
            self.path_label.config(text="パス/URL/ターゲット:")
            self.path_entry.pack(fill="x", padx=5)
            self.target_page_combo.pack_forget()
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Default to showing path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame

    def clear_button_form(self):
        """フォームの入力内容を初期状態に戻す。"""
        self.form_entries[C.ConfigKey.NAME].set("")
        self.form_entries[C.ConfigKey.ACTION].set("")
        self.form_entries[C.ConfigKey.PATH].set("")
        self.form_entries[C.ConfigKey.BASE_URL].set("") # Clear base_url
        self.current_parameters = [] # Clear current parameters
        self.update_parameter_listbox() # Update listbox
        self.path_label.config(text="パス/URL/ターゲット:")
        self.path_entry.pack(fill="x", padx=5)
        self.target_page_combo.pack_forget()
        self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Default to showing path entry
        self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        self._loaded_ref = None
        self._reset_form_dirty()

    def update_parameter_listbox(self):
        """パラメータ一覧の表示を更新する。"""
        self.parameter_listbox.delete(0, tk.END)
        for param in self.current_parameters:
            display_text = f"{param.get(C.ConfigKey.NAME, '')}: {param.get(C.ConfigKey.TYPE, '')}"
            if param.get(C.ConfigKey.LABEL):
                display_text += f" ({param[C.ConfigKey.LABEL]})"
            self.parameter_listbox.insert(tk.END, display_text)

    def add_parameter(self):
        """パラメータ追加の編集ダイアログを開く。"""
        self.open_parameter_editor_window()

    def edit_parameter(self):
        """選択中のパラメータを編集する。"""
        selected_indices = self.parameter_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "編集するパラメータを選択してください。")
            return
        idx = selected_indices[0]
        param_data = self.current_parameters[idx]
        self.open_parameter_editor_window(idx, param_data)

    def delete_parameter(self):
        """選択中のパラメータを削除する。"""
        selected_indices = self.parameter_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "削除するパラメータを選択してください。")
            return
        idx = selected_indices[0]
        if messagebox.askyesno("確認", "選択したパラメータを削除しますか？"):
            del self.current_parameters[idx]
            self.update_parameter_listbox()
            self._mark_form_dirty()

    def open_parameter_editor_window(self, index=None, param_data=None):
        """パラメータ編集ウィンドウを開き、結果を取り込む。"""
        editor_window = ParameterEditor(self, index, param_data)
        self.master.wait_window(editor_window) # Wait for the editor window to close
        if editor_window.result_param_data: # If data was saved
            if index is not None: # Editing existing parameter
                self.current_parameters[index] = editor_window.result_param_data
            else: # Adding new parameter
                self.current_parameters.append(editor_window.result_param_data)
            self.update_parameter_listbox()
            self._mark_form_dirty()

    def save_form_data(self):
        """フォーム入力を、編集中のページ設定へ保存する。

        表示中のタブではなく、フォームに読み込んだ時点のページ（_form_page）へ
        保存する。タブを切り替えても内容が別ページへ紛れ込まない。
        """
        page_name = getattr(self, "_form_page", None)
        if not page_name:
            # フォールバック: 表示中タブ
            pages_notebook = self.pages_widgets["pages_notebook"]
            try:
                current_frame = pages_notebook.nametowidget(pages_notebook.select())
                page_name = self.page_frame_to_name.get(current_frame)
            except Exception:
                page_name = None
        if not page_name or page_name not in self.config.get(C.ConfigKey.PAGES, {}):
            messagebox.showerror("エラー", "保存先のページを特定できませんでした。")
            return
        self._form_page = page_name

        loaded_ref = getattr(self, "_loaded_ref", None)
        edit_idx = loaded_ref[1] if (loaded_ref and loaded_ref[0] == page_name) else None

        new_entry = {
            C.ConfigKey.NAME: self.form_entries[C.ConfigKey.NAME].get(),
            C.ConfigKey.ACTION: self.form_entries[C.ConfigKey.ACTION].get(),
        }
        # 新規追加時、activeをTrueに設定
        if edit_idx is None:
            new_entry[C.ConfigKey.ACTIVE] = True

        # アクションに応じてキー名を変える
        action = new_entry[C.ConfigKey.ACTION]
        if action == C.Action.OPEN_DIRECTORY:
            new_entry[C.ConfigKey.PATH] = self.form_entries[C.ConfigKey.PATH].get()
        elif action == C.Action.OPEN_URL:
            new_entry[C.ConfigKey.URL] = self.form_entries[C.ConfigKey.PATH].get()
        elif action == C.Action.SHOW_PAGE:
            target_display_or_id = self.form_entries[C.ConfigKey.PATH].get()
            new_entry[C.ConfigKey.TARGET] = self.page_display_to_id.get(target_display_or_id, target_display_or_id)
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            new_entry[C.ConfigKey.BASE_URL] = self.form_entries[C.ConfigKey.BASE_URL].get()
            new_entry[C.ConfigKey.PARAMETERS] = self.current_parameters

        if not new_entry[C.ConfigKey.NAME]:
            messagebox.showerror("エラー", "名前は必須です。")
            return

        entries = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES]
        if edit_idx is not None and 0 <= edit_idx < len(entries): # 編集モード
            # activeの状態は変更しない
            new_entry[C.ConfigKey.ACTIVE] = entries[edit_idx].get(C.ConfigKey.ACTIVE, True)
            entries[edit_idx] = new_entry
        else: # 追加モード
            entries.append(new_entry)

        self._populate_page_listbox(page_name) # リストボックスを更新
        self._set_status(f"「{new_entry[C.ConfigKey.NAME]}」を保存しました。")
        self.clear_button_form() # フォームをクリア（未保存フラグも解除）
        self._form_page = page_name  # 続けて同じページへ追加できるよう保持
