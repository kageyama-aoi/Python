import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from . import constants as C
from .config_manager import ConfigManager
import copy

class SettingsEditor(tk.Toplevel):
    def __init__(self, master, config_manager: ConfigManager, on_save_callback=None):
        super().__init__(master)
        self.title("設定エディタ")
        self.config_manager = config_manager
        self.on_save_callback = on_save_callback
        self.geometry("700x600")

        # 編集用の一時的なconfigのコピーを作成
        self.config = copy.deepcopy(self.config_manager.get_config())

        self.current_parameters = []
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Notebook (タブ)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        # ページ編集タブ
        pages_tab = ttk.Frame(notebook)
        notebook.add(pages_tab, text="ページ編集")
        self.create_pages_tab(pages_tab)

        # 設定タブ
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="基本設定")
        self.create_settings_tab(settings_tab)

        # 保存ボタン
        save_button = ttk.Button(main_frame, text="保存して閉じる", command=self.save_config)
        save_button.pack(pady=10)

    def create_settings_tab(self, parent):
        # settingsの編集
        settings_frame = ttk.LabelFrame(parent, text="ウィンドウ設定")
        settings_frame.pack(padx=10, pady=10, fill="x")

        self.settings_vars = {}
        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        for key, value in settings.items():
            if isinstance(value, list):
                value = ", ".join(map(str, value))
            
            frame = ttk.Frame(settings_frame)
            frame.pack(fill="x", pady=2)
            
            label = ttk.Label(frame, text=key)
            label.pack(side="left", padx=5)
            
            var = tk.StringVar(value=value)
            self.settings_vars[key] = var
            
            entry = ttk.Entry(frame, textvariable=var)
            entry.pack(side="right", expand=True, fill="x")

    def create_pages_tab(self, parent):
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 左ペイン (リスト) ---
        left_pane = ttk.Frame(paned_window)
        paned_window.add(left_pane, weight=1)

        pages_notebook = ttk.Notebook(left_pane)
        pages_notebook.pack(fill="both", expand=True)
        self.pages_widgets = {"pages_notebook": pages_notebook}

        pages = self.config.get(C.ConfigKey.PAGES, {})
        for page_name, page_data in pages.items():
            list_frame = ttk.Frame(pages_notebook)
            pages_notebook.add(list_frame, text=page_name)

            listbox = tk.Listbox(list_frame)
            listbox.pack(fill="both", expand=True)
            listbox.bind("<<ListboxSelect>>", lambda event, p=page_name: self.on_listbox_select(event, p))

            for entry in page_data.get(C.ConfigKey.ENTRIES, []):
                listbox.insert(tk.END, entry.get(C.ConfigKey.NAME, "(無名)"))

            button_frame = ttk.Frame(list_frame)
            button_frame.pack(fill="x", pady=5)

            add_button = ttk.Button(button_frame, text="追加", command=lambda p=page_name: self.add_button(p))
            add_button.pack(side="left", padx=2)

            up_button = ttk.Button(button_frame, text="上へ", command=lambda p=page_name: self.move_item(p, "up"))
            up_button.pack(side="left", padx=2)

            down_button = ttk.Button(button_frame, text="下へ", command=lambda p=page_name: self.move_item(p, "down"))
            down_button.pack(side="left", padx=2)

            self.pages_widgets[page_name] = {"listbox": listbox}

        # --- 右ペイン (フォーム) ---
        right_pane = ttk.LabelFrame(paned_window, text="ボタン設定")
        paned_window.add(right_pane, weight=1)
        self.create_button_form(right_pane)

    def add_button(self, page_name):
        # 選択を解除して追加モードにする
        listbox = self.pages_widgets[page_name]["listbox"]
        listbox.selection_clear(0, tk.END)
        self.clear_button_form()

    def on_listbox_select(self, event, page_name):
        listbox = event.widget
        selected_indices = listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        entry_data = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES][idx]

        # フォームにデータを表示
        self.form_entries[C.ConfigKey.NAME].set(entry_data.get(C.ConfigKey.NAME, ""))
        action = entry_data.get(C.ConfigKey.ACTION, "")
        self.form_entries[C.ConfigKey.ACTION].set(action)

        # path/url/target の値を取得
        path_value = ""
        if action == C.Action.OPEN_DIRECTORY:
            path_value = entry_data.get(C.ConfigKey.PATH, "")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.OPEN_URL:
            path_value = entry_data.get(C.ConfigKey.URL, "")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.SHOW_PAGE:
            path_value = entry_data.get(C.ConfigKey.TARGET, "")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            self.form_entries[C.ConfigKey.BASE_URL].set(entry_data.get(C.ConfigKey.BASE_URL, ""))
            self.current_parameters = entry_data.get(C.ConfigKey.PARAMETERS, [])
            self.update_parameter_listbox()
            self.path_entry_frame.pack_forget() # Hide path entry
            self.parameterized_url_frame.pack(fill="both", expand=True, padx=5, pady=2) # Show parameterized URL frame
        else:
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Default to showing path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame

        self.form_entries[C.ConfigKey.PATH].set(path_value)

        # ラベルも更新
        self.on_action_change(None) # eventオブジェクトは使わないのでNone

    def move_item(self, page_name, direction):
        listbox = self.pages_widgets[page_name]["listbox"]
        selected_indices = listbox.curselection()

        if not selected_indices:
            return

        idx = selected_indices[0]

        if direction == "up" and idx > 0:
            new_idx = idx - 1
        elif direction == "down" and idx < listbox.size() - 1:
            new_idx = idx + 1
        else:
            return

        # configのentriesを入れ替え
        entries = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES]
        entries[idx], entries[new_idx] = entries[new_idx], entries[idx]

        # リストボックスの表示を更新
        listbox.delete(0, tk.END)
        for entry in entries:
            listbox.insert(tk.END, entry.get(C.ConfigKey.NAME, "(無名)"))
        
        # 選択状態を復元
        listbox.selection_set(new_idx)
        listbox.activate(new_idx)

    def on_action_change(self, event):
        action = self.form_entries[C.ConfigKey.ACTION].get()
        if action == C.Action.OPEN_DIRECTORY:
            self.path_label.config(text="開くフォルダのパス:")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.OPEN_URL:
            self.path_label.config(text="開くWebサイトのURL:")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.SHOW_PAGE:
            self.path_label.config(text="表示するページ名:")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Show path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            self.path_entry_frame.pack_forget() # Hide path entry
            self.parameterized_url_frame.pack(fill="both", expand=True, padx=5, pady=2) # Show parameterized URL frame
        else:
            self.path_label.config(text="パス/URL/ターゲット:")
            self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Default to showing path entry
            self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame

    def clear_button_form(self):
        self.form_entries[C.ConfigKey.NAME].set("")
        self.form_entries[C.ConfigKey.ACTION].set("")
        self.form_entries[C.ConfigKey.PATH].set("")
        self.form_entries[C.ConfigKey.BASE_URL].set("") # Clear base_url
        self.current_parameters = [] # Clear current parameters
        self.update_parameter_listbox() # Update listbox
        self.path_label.config(text="パス/URL/ターゲット:")
        self.path_entry_frame.pack(fill="x", padx=5, pady=2) # Default to showing path entry
        self.parameterized_url_frame.pack_forget() # Hide parameterized URL frame

    def create_button_form(self, parent):
        self.form_entries = {}
        
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
        path_entry = ttk.Entry(self.path_entry_frame, textvariable=path_var)
        path_entry.pack(fill="x", padx=5)
        self.form_entries[C.ConfigKey.PATH] = path_var # path, url, targetを同じEntryで使い回す

        # --- Parameterized URL Settings (特殊なボタン用) ---
        self.parameterized_url_frame = ttk.LabelFrame(parent, text="パラメータ設定")
        # Initially hidden
        # self.parameterized_url_frame.pack(fill="both", expand=True, padx=5, pady=2)

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

    def update_parameter_listbox(self):
        self.parameter_listbox.delete(0, tk.END)
        for param in self.current_parameters:
            display_text = f"{param.get(C.ConfigKey.NAME, '')}: {param.get(C.ConfigKey.TYPE, '')}"
            if param.get(C.ConfigKey.LABEL):
                display_text += f" ({param[C.ConfigKey.LABEL]})"
            self.parameter_listbox.insert(tk.END, display_text)

    def add_parameter(self):
        self.open_parameter_editor_window()

    def edit_parameter(self):
        selected_indices = self.parameter_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "編集するパラメータを選択してください。")
            return
        idx = selected_indices[0]
        param_data = self.current_parameters[idx]
        self.open_parameter_editor_window(idx, param_data)

    def delete_parameter(self):
        selected_indices = self.parameter_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "削除するパラメータを選択してください。")
            return
        idx = selected_indices[0]
        if messagebox.askyesno("確認", "選択したパラメータを削除しますか？"):
            del self.current_parameters[idx]
            self.update_parameter_listbox()

    def open_parameter_editor_window(self, index=None, param_data=None):
        editor_window = ParameterEditor(self, index, param_data)
        self.master.wait_window(editor_window) # Wait for the editor window to close
        if editor_window.result_param_data: # If data was saved
            if index is not None: # Editing existing parameter
                self.current_parameters[index] = editor_window.result_param_data
            else: # Adding new parameter
                self.current_parameters.append(editor_window.result_param_data)
            self.update_parameter_listbox()

    def save_form_data(self):
        # 現在アクティブなページ名を取得
        pages_notebook = self.pages_widgets["pages_notebook"]
        page_name = pages_notebook.tab(pages_notebook.select(), "text")
        listbox = self.pages_widgets[page_name]["listbox"]

        new_entry = {
            C.ConfigKey.NAME: self.form_entries[C.ConfigKey.NAME].get(),
            C.ConfigKey.ACTION: self.form_entries[C.ConfigKey.ACTION].get(),
        }
        # アクションに応じてキー名を変える
        action = new_entry[C.ConfigKey.ACTION]
        if action == C.Action.OPEN_DIRECTORY:
            new_entry[C.ConfigKey.PATH] = self.form_entries[C.ConfigKey.PATH].get()
        elif action == C.Action.OPEN_URL:
            new_entry[C.ConfigKey.URL] = self.form_entries[C.ConfigKey.PATH].get()
        elif action == C.Action.SHOW_PAGE:
            new_entry[C.ConfigKey.TARGET] = self.form_entries[C.ConfigKey.PATH].get()
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            new_entry[C.ConfigKey.BASE_URL] = self.form_entries[C.ConfigKey.BASE_URL].get()
            new_entry[C.ConfigKey.PARAMETERS] = self.current_parameters

        if not new_entry[C.ConfigKey.NAME]:
            messagebox.showerror("エラー", "名前は必須です。")
            return

        selected_indices = listbox.curselection()
        if selected_indices: # 編集モード
            idx = selected_indices[0]
            self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES][idx] = new_entry
            listbox.delete(idx)
            listbox.insert(idx, new_entry[C.ConfigKey.NAME])
            listbox.selection_set(idx) # 選択状態を維持
        else: # 追加モード
            self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES].append(new_entry)
            listbox.insert(tk.END, new_entry[C.ConfigKey.NAME])

        self.clear_button_form()

    def save_config(self):
        # settingsの保存
        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        for key, var in self.settings_vars.items():
            value = var.get()
            if key == C.ConfigKey.RESIZABLE:
                try:
                    # 'True, False' のような文字列を [True, False] のようなリストに変換
                    settings[key] = [
                        v.strip().lower() in ('true', '1', 't', 'y', 'yes') 
                        for v in value.split(',')
                    ]
                except Exception as e:
                    messagebox.showerror("入力エラー", f"'{C.ConfigKey.RESIZABLE}' の値は 'True, False' のようにカンマ区切りの真偽値で入力してください。\nエラー: {e}")
                    return
            else:
                settings[key] = value
        self.config[C.ConfigKey.SETTINGS] = settings

        # 新しい設定をConfigManager経由で保存
        if self.config_manager.save_config(self.config):
            messagebox.showinfo("成功", "設定を保存しました。")
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        else:
            # 保存失敗のメッセージはConfigManagerが表示するのでここでは不要
            # messagebox.showerror("エラー", "設定の保存に失敗しました。詳細はコンソールを確認してください。")
            pass