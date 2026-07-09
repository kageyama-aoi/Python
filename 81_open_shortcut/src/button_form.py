"""ボタン設定フォーム（右ペイン：アクション別入力・パラメータ編集・フォーム保存）。

SettingsEditor に組み込むミックスイン。ページ編集タブ（pages_tab.py）の
リスト選択と連動してフォーム内容を切り替える。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from . import constants as C


class ButtonFormMixin:
    """ボタン設定フォームの構築と保存を提供する。"""

    def create_button_form(self, parent):
        """右ペインのボタン設定フォームを構築する。"""
        self.form_entries = {}
        self._build_page_selector_maps()

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
        action_combo.bind("<<ComboboxSelected>>", self.on_action_change)
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

    def open_parameter_editor_window(self, index=None, param_data=None):
        """パラメータ編集ウィンドウを開き、結果を取り込む。"""
        # NOTE: ParameterEditor class is not defined in this file. Assuming it's defined elsewhere or a placeholder.
        editor_window = ParameterEditor(self, index, param_data)
        self.master.wait_window(editor_window) # Wait for the editor window to close
        if editor_window.result_param_data: # If data was saved
            if index is not None: # Editing existing parameter
                self.current_parameters[index] = editor_window.result_param_data
            else: # Adding new parameter
                self.current_parameters.append(editor_window.result_param_data)
            self.update_parameter_listbox()

    def save_form_data(self):
        """フォーム入力を現在のページ設定に保存する。"""
        # 現在アクティブなページ名を取得
        pages_notebook = self.pages_widgets["pages_notebook"]
        current_frame = pages_notebook.nametowidget(pages_notebook.select())
        page_name = self.page_frame_to_name.get(current_frame)
        if not page_name:
            messagebox.showerror("エラー", "現在のページ情報を取得できませんでした。")
            return
        listbox = self.pages_widgets[page_name]["listbox"]

        new_entry = {
            C.ConfigKey.NAME: self.form_entries[C.ConfigKey.NAME].get(),
            C.ConfigKey.ACTION: self.form_entries[C.ConfigKey.ACTION].get(),
        }
        # 新規追加時、activeをTrueに設定
        if not listbox.curselection():
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

        selected_indices = listbox.curselection()
        if selected_indices: # 編集モード
            idx = selected_indices[0]
            # activeの状態は変更しない
            new_entry[C.ConfigKey.ACTIVE] = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES][idx].get(C.ConfigKey.ACTIVE, True)
            self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES][idx] = new_entry

        else: # 追加モード
            self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES].append(new_entry)

        self._populate_page_listbox(page_name) # リストボックスを更新
        self.clear_button_form() # フォームをクリア
