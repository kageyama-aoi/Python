"""設定編集ウィンドウのUIと操作を提供するモジュール。"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import re
from . import constants as C
from .config_manager import ConfigManager
import copy

class SettingsEditor(tk.Toplevel):
    """設定ファイル編集用のGUIを提供するウィンドウ。"""
    SETTING_LABELS = {
        "window_title": "ウィンドウタイトル",
        "geometry": "ウィンドウサイズ",
        "resizable": "サイズ変更可否",
        "icon_folder": "アイコンフォルダ",
        "window_icon": "ウィンドウアイコン",
        "default_button_icon": "デフォルトボタンアイコン",
        "initial_page": "起動時のページ",
        "menu_order": "メニュー表示順",
    }
    MENU_ORDER_DISPLAY_TO_VALUE = {
        "通常": "normal",
        "逆順": "reverse",
        "全体設定に従う": "global",
    }
    MENU_ORDER_VALUE_TO_DISPLAY = {
        value: key for key, value in MENU_ORDER_DISPLAY_TO_VALUE.items()
    }

    def __init__(self, master, config_manager: ConfigManager, on_save_callback=None):
        """設定編集ウィンドウを初期化し、初期フォームを構築する。"""
        super().__init__(master)
        self.title("設定エディタ")
        self.config_manager = config_manager
        self.on_save_callback = on_save_callback
        self.geometry("700x600")

        # 編集用の一時的なconfigのコピーを作成
        self.config = copy.deepcopy(self.config_manager.get_config())

        self.current_parameters = []
        self.create_widgets()

    def _format_setting_label(self, key: str) -> str:
        """設定キーを「日本語（英語）」形式のラベルへ変換する。"""
        key_value = key.value if hasattr(key, "value") else key
        ja = self.SETTING_LABELS.get(key_value, key_value)
        return f"{ja} ({key_value})"

    def _format_page_tab_label(self, page_name: str, page_data: dict) -> str:
        """ページタブを「日本語（英語）」形式で表示する。"""
        title = page_data.get(C.ConfigKey.TITLE, page_name)
        # 日本語タイトル内の英語補足（例: [Tframe], (memo)）を除去して重複表記を防ぐ
        cleaned_title = re.sub(r"\s*[\[\(（]\s*[A-Za-z0-9_\- ]+\s*[\]\)）]\s*", "", str(title)).strip()
        if not cleaned_title:
            cleaned_title = page_name
        return f"{cleaned_title} ({page_name})"

    def _build_page_selector_maps(self):
        """ページ選択用の表示名<->IDマップを構築する。"""
        self.page_display_to_id = {}
        self.page_id_to_display = {}
        pages = self.config.get(C.ConfigKey.PAGES, {})
        for page_name, page_data in pages.items():
            display_label = self._format_page_tab_label(page_name, page_data)
            self.page_display_to_id[display_label] = page_name
            self.page_id_to_display[page_name] = display_label

    def create_widgets(self):
        """ウィンドウ全体のレイアウトとタブを構築する。"""
        self._build_page_selector_maps()
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

        # 操作結果を非モーダルで表示するステータス
        self.status_var = tk.StringVar(value="準備完了")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(fill="x", pady=(8, 0))

        # 保存ボタン
        save_button = ttk.Button(main_frame, text="保存して閉じる", command=self.save_config)
        save_button.pack(pady=10)

    def _set_status(self, message: str):
        """設定画面下部のステータスを更新する。"""
        if hasattr(self, "status_var"):
            self.status_var.set(message)

    def create_settings_tab(self, parent):
        """基本設定タブの入力フォームを作成する。"""
        # settingsの編集
        settings_frame = ttk.LabelFrame(parent, text="ウィンドウ設定")
        settings_frame.pack(padx=10, pady=10, fill="x")

        self.settings_vars = {}
        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        for key, value in settings.items():
            if key in (C.ConfigKey.MENU_ORDER, C.ConfigKey.INITIAL_PAGE):
                continue

            if isinstance(value, list):
                value = ", ".join(map(str, value))
            
            frame = ttk.Frame(settings_frame)
            frame.pack(fill="x", pady=2)
            
            label = ttk.Label(frame, text=self._format_setting_label(key))
            label.pack(side="left", padx=5)
            
            var = tk.StringVar(value=value)
            self.settings_vars[key] = var
            
            entry = ttk.Entry(frame, textvariable=var)
            entry.pack(side="right", expand=True, fill="x")

        # 初期ページはページ一覧から選択して入力ミスを防ぐ
        initial_page_frame = ttk.Frame(settings_frame)
        initial_page_frame.pack(fill="x", pady=2)
        initial_page_label = ttk.Label(initial_page_frame, text=self._format_setting_label(C.ConfigKey.INITIAL_PAGE))
        initial_page_label.pack(side="left", padx=5)

        page_names = list(self.config.get(C.ConfigKey.PAGES, {}).keys())
        page_display_names = list(self.page_display_to_id.keys())
        initial_page_value = settings.get(C.ConfigKey.INITIAL_PAGE, "")
        if page_names and initial_page_value not in page_names:
            initial_page_value = page_names[0]
        initial_page_display = self.page_id_to_display.get(initial_page_value, initial_page_value)
        if page_display_names and initial_page_display not in page_display_names:
            initial_page_display = page_display_names[0]

        initial_page_var = tk.StringVar(value=initial_page_display)
        self.settings_vars[C.ConfigKey.INITIAL_PAGE] = initial_page_var

        initial_page_combo = ttk.Combobox(
            initial_page_frame,
            textvariable=initial_page_var,
            values=page_display_names,
            state="readonly"
        )
        initial_page_combo.pack(side="right", expand=True, fill="x")
        self.initial_page_combo = initial_page_combo

        # メニュー表示順は選択式で編集しやすくする
        menu_order_frame = ttk.Frame(settings_frame)
        menu_order_frame.pack(fill="x", pady=2)
        menu_order_label = ttk.Label(menu_order_frame, text=self._format_setting_label(C.ConfigKey.MENU_ORDER))
        menu_order_label.pack(side="left", padx=5)

        menu_order_value = settings.get(C.ConfigKey.MENU_ORDER, "normal")
        if menu_order_value not in ("normal", "reverse"):
            menu_order_value = "normal"

        menu_order_var = tk.StringVar(value=self.MENU_ORDER_VALUE_TO_DISPLAY[menu_order_value])
        self.settings_vars[C.ConfigKey.MENU_ORDER] = menu_order_var

        menu_order_combo = ttk.Combobox(
            menu_order_frame,
            textvariable=menu_order_var,
            values=["通常", "逆順"],
            state="readonly"
        )
        menu_order_combo.pack(side="right", expand=True, fill="x")

        # ページ順は手動UIを廃止し、遷移先(show_page)から自動計算する
        self.page_order_ids = list(self.config.get(C.ConfigKey.PAGES, {}).keys())

        # show_page の遷移先を手動編集する
        transition_frame = ttk.LabelFrame(parent, text="ページ遷移先 (show_page)")
        transition_frame.pack(padx=10, pady=(0, 10), fill="x")
        self._build_transition_target_editor(transition_frame)

    def _build_transition_target_editor(self, parent):
        """show_page エントリの遷移先編集UIを作成する。"""
        self.transition_target_rows = []
        page_display_names = list(self.page_display_to_id.keys())
        pages = self.config.get(C.ConfigKey.PAGES, {})

        row_count = 0
        for page_id, page_data in pages.items():
            entries = page_data.get(C.ConfigKey.ENTRIES, [])
            for entry in entries:
                if entry.get(C.ConfigKey.ACTION) != C.Action.SHOW_PAGE:
                    continue

                row_count += 1
                row = ttk.Frame(parent)
                row.pack(fill="x", padx=5, pady=2)

                entry_name = entry.get(C.ConfigKey.NAME, "(無名)")
                from_label = ttk.Label(row, text=f"{self.page_id_to_display.get(page_id, page_id)}")
                from_label.pack(side="left", padx=(0, 6))

                target_id = entry.get(C.ConfigKey.TARGET, "")
                target_display = self.page_id_to_display.get(target_id, target_id)
                target_var = tk.StringVar(value=target_display)
                target_combo = ttk.Combobox(row, textvariable=target_var, values=page_display_names, state="readonly")
                target_combo.pack(side="right", fill="x", expand=True)
                target_combo.bind("<<ComboboxSelected>>", self._on_transition_target_change)

                self.transition_target_rows.append({
                    "page_id": page_id,
                    "entry_ref": entry,
                    "entry_name": entry_name,
                    "target_var": target_var,
                    "target_combo": target_combo,
                })

        if row_count == 0:
            ttk.Label(parent, text="show_page の設定がありません。").pack(anchor="w", padx=5, pady=4)

    def _on_transition_target_change(self, event=None):
        """遷移先変更時にページ順を再計算してUIへ反映する。"""
        self._recompute_page_order_from_transitions()
        self._set_status("遷移先に合わせてページ順を更新しました。")

    def _get_current_initial_page_id(self) -> str:
        """現在選択中の初期ページIDを返す。"""
        initial_value = ""
        if hasattr(self, "settings_vars") and C.ConfigKey.INITIAL_PAGE in self.settings_vars:
            initial_value = self.settings_vars[C.ConfigKey.INITIAL_PAGE].get()
        return self.page_display_to_id.get(initial_value, initial_value)

    def _set_page_order_by_ids(self, ordered_page_ids: list[str]):
        """ページID配列を内部のページ順へ反映する。"""
        self.page_order_ids = [
            page_id for page_id in ordered_page_ids
            if page_id in self.page_id_to_display
        ]

    def _recompute_page_order_from_transitions(self):
        """
        show_page遷移をたどってページ順を再計算する。
        先頭は初期ページ、以降は「各ページの最初のshow_page target」を優先する。
        """
        if not hasattr(self, "transition_target_rows"):
            return

        next_map = {}
        for row in self.transition_target_rows:
            source_id = row.get("page_id")
            target_display_or_id = row.get("target_var").get() if row.get("target_var") else ""
            target_id = self.page_display_to_id.get(target_display_or_id, target_display_or_id)
            if source_id and target_id and target_id in self.page_id_to_display and source_id not in next_map:
                next_map[source_id] = target_id

        existing_order = self._get_page_order_ids()
        if not existing_order:
            existing_order = list(self.config.get(C.ConfigKey.PAGES, {}).keys())

        start_page_id = self._get_current_initial_page_id()
        if start_page_id not in self.page_id_to_display:
            start_page_id = existing_order[0] if existing_order else ""

        ordered = []
        seen = set()
        current = start_page_id
        while current and current not in seen and current in self.page_id_to_display:
            ordered.append(current)
            seen.add(current)
            current = next_map.get(current)

        for page_id in existing_order:
            if page_id not in seen and page_id in self.page_id_to_display:
                ordered.append(page_id)
                seen.add(page_id)

        self._set_page_order_by_ids(ordered)
        self._sync_page_tabs_with_order()
        self._sync_initial_page_choices_with_order()
        self._sync_transition_target_choices_with_order()

    def _get_page_order_ids(self) -> list[str]:
        """現在のページ順（ページID配列）を返す。"""
        if hasattr(self, "page_order_ids") and self.page_order_ids:
            return list(self.page_order_ids)
        return list(self.config.get(C.ConfigKey.PAGES, {}).keys())

    def _sync_page_tabs_with_order(self):
        """ページ順リストの順序へページ編集タブの順を合わせる。"""
        notebook = self.pages_widgets.get("pages_notebook") if hasattr(self, "pages_widgets") else None
        if not notebook:
            return

        for page_id in self._get_page_order_ids():
            frame = self.page_name_to_frame.get(page_id)
            if frame:
                notebook.insert("end", frame)

    def _sync_initial_page_choices_with_order(self):
        """ページ順リストの順序へ初期ページプルダウン候補の順を合わせる。"""
        if not hasattr(self, "initial_page_combo"):
            return
        ordered_displays = [
            self.page_id_to_display[page_id]
            for page_id in self._get_page_order_ids()
            if page_id in self.page_id_to_display
        ]
        self.initial_page_combo.config(values=ordered_displays)

    def _sync_transition_target_choices_with_order(self):
        """ページ順リストの順序へ遷移先プルダウン候補の順を合わせる。"""
        if not hasattr(self, "transition_target_rows"):
            return
        ordered_displays = [
            self.page_id_to_display[page_id]
            for page_id in self._get_page_order_ids()
            if page_id in self.page_id_to_display
        ]
        for row in self.transition_target_rows:
            target_var = row.get("target_var")
            target_combo = row.get("target_combo")
            current = target_var.get() if target_var else ""
            combo_values = ordered_displays
            if current and current not in combo_values:
                combo_values = combo_values + [current]
            if target_combo:
                target_combo.config(values=combo_values)

    def create_pages_tab(self, parent):
        """ページ一覧とボタン設定フォームを持つタブを作成する。"""
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 左ペイン (リスト) ---
        left_pane = ttk.Frame(paned_window)
        paned_window.add(left_pane, weight=1)

        pages_notebook = ttk.Notebook(left_pane)
        pages_notebook.pack(fill="both", expand=True)
        self.pages_widgets = {"pages_notebook": pages_notebook}
        self.page_menu_order_vars = {}
        self.page_frame_to_name = {}
        self.page_name_to_frame = {}

        pages = self.config.get(C.ConfigKey.PAGES, {})
        tab_order = list(pages.items())

        for page_name, page_data in tab_order:
            list_frame = ttk.Frame(pages_notebook)
            pages_notebook.add(list_frame, text=self._format_page_tab_label(page_name, page_data))
            self.page_frame_to_name[list_frame] = page_name
            self.page_name_to_frame[page_name] = list_frame

            # ページごとのメニュー表示順
            page_order_frame = ttk.Frame(list_frame)
            page_order_frame.pack(fill="x", pady=2)

            ttk.Label(page_order_frame, text="表示順:").pack(side="left", padx=2)
            page_menu_order = page_data.get(C.ConfigKey.MENU_ORDER, "global")
            if page_menu_order not in ("global", "normal", "reverse"):
                page_menu_order = "global"

            page_menu_order_var = tk.StringVar(value=self.MENU_ORDER_VALUE_TO_DISPLAY[page_menu_order])
            self.page_menu_order_vars[page_name] = page_menu_order_var

            page_order_combo = ttk.Combobox(
                page_order_frame,
                textvariable=page_menu_order_var,
                values=["全体設定に従う", "通常", "逆順"],
                state="readonly",
                width=12,
            )
            page_order_combo.pack(side="left", padx=2)

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

            # 非表示/表示ボタンを追加
            hide_button = ttk.Button(button_frame, text="非表示にする", command=lambda p=page_name: self.hide_item(p))
            hide_button.pack(side="left", padx=2)

            show_button = ttk.Button(button_frame, text="表示する", command=lambda p=page_name: self.show_item(p))
            show_button.pack(side="left", padx=2)

            self.pages_widgets[page_name] = {
                "listbox": listbox,
                "add_button": add_button,
                "up_button": up_button,
                "down_button": down_button,
                "hide_button": hide_button,
                "show_button": show_button,
            }
            self._populate_page_listbox(page_name) # Populate listbox initially
            self._update_page_buttons_state(page_name)

        # --- 右ペイン (フォーム) ---
        right_pane = ttk.LabelFrame(paned_window, text="ボタン設定")
        paned_window.add(right_pane, weight=1)
        self.create_button_form(right_pane)

    def _populate_page_listbox(self, page_name):
        """
        指定されたページのリストボックスをクリアし、configデータに基づいて再構築する。
        activeプロパティに基づいて表示を調整する。
        """
        listbox = self.pages_widgets[page_name]["listbox"]
        listbox.delete(0, tk.END)
        entries = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES]
        for i, entry in enumerate(entries):
            display_name = entry.get(C.ConfigKey.NAME, "(無名)")
            if not entry.get(C.ConfigKey.ACTIVE, True): # default True if not present
                display_name = f"（非表示）{display_name}"
            listbox.insert(tk.END, display_name)
            # 後でactive状態を示すためにタグ付けすることも可能だが、今回はテキストで示す
            # if not entry.get(C.ConfigKey.ACTIVE, True):
            #     listbox.itemconfig(i, fg="grey")
        self._update_page_buttons_state(page_name)

    def _update_page_buttons_state(self, page_name):
        """ページ操作ボタンの活性状態を現在の選択状態に合わせて更新する。"""
        page_widgets = self.pages_widgets.get(page_name, {})
        listbox = page_widgets.get("listbox")
        if not listbox:
            return

        add_button = page_widgets.get("add_button")
        up_button = page_widgets.get("up_button")
        down_button = page_widgets.get("down_button")
        hide_button = page_widgets.get("hide_button")
        show_button = page_widgets.get("show_button")

        if add_button:
            add_button.config(state="normal")

        selected = listbox.curselection()
        if not selected:
            if up_button:
                up_button.config(state="disabled")
            if down_button:
                down_button.config(state="disabled")
            if hide_button:
                hide_button.config(state="disabled")
            if show_button:
                show_button.config(state="disabled")
            return

        idx = selected[0]
        entries = self.config.get(C.ConfigKey.PAGES, {}).get(page_name, {}).get(C.ConfigKey.ENTRIES, [])
        size = listbox.size()
        is_active = True
        if 0 <= idx < len(entries):
            is_active = entries[idx].get(C.ConfigKey.ACTIVE, True)

        if up_button:
            up_button.config(state="normal" if idx > 0 else "disabled")
        if down_button:
            down_button.config(state="normal" if idx < size - 1 else "disabled")
        if hide_button:
            hide_button.config(state="normal" if is_active else "disabled")
        if show_button:
            show_button.config(state="normal" if not is_active else "disabled")

    def hide_item(self, page_name):
        """選択中の項目を非表示として扱う。"""
        listbox = self.pages_widgets[page_name]["listbox"]
        selected_indices = listbox.curselection()

        if not selected_indices:
            messagebox.showwarning("警告", "非表示にする項目を選択してください。")
            return

        idx = selected_indices[0]
        entries = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES]
        
        if entries[idx].get(C.ConfigKey.ACTIVE, True) is False: # Already hidden
            messagebox.showinfo("情報", "選択された項目は既に非表示です。")
            return

        entries[idx][C.ConfigKey.ACTIVE] = False
        self._populate_page_listbox(page_name)
        self.clear_button_form()
        self._set_status(f"項目「{entries[idx].get(C.ConfigKey.NAME, '(無名)')}」を非表示にしました。")

    def show_item(self, page_name):
        """選択中の項目を表示状態に戻す。"""
        listbox = self.pages_widgets[page_name]["listbox"]
        selected_indices = listbox.curselection()

        if not selected_indices:
            messagebox.showwarning("警告", "表示する項目を選択してください。")
            return

        idx = selected_indices[0]
        entries = self.config[C.ConfigKey.PAGES][page_name][C.ConfigKey.ENTRIES]

        if entries[idx].get(C.ConfigKey.ACTIVE, True) is True: # Already shown
            messagebox.showinfo("情報", "選択された項目は既に表示されています。")
            return
            
        entries[idx][C.ConfigKey.ACTIVE] = True
        self._populate_page_listbox(page_name)
        self.clear_button_form()
        self._set_status(f"項目「{entries[idx].get(C.ConfigKey.NAME, '(無名)')}」を表示しました。")

    def add_button(self, page_name):
        """新規追加モードに切り替える。"""
        # 選択を解除して追加モードにする
        listbox = self.pages_widgets[page_name]["listbox"]
        listbox.selection_clear(0, tk.END)
        self.clear_button_form()
        self._update_page_buttons_state(page_name)

    def on_listbox_select(self, event, page_name):
        """リストボックス選択に応じてフォームへ値を反映する。"""
        listbox = event.widget
        selected_indices = listbox.curselection()
        if not selected_indices:
            self.clear_button_form() # 選択解除時にフォームをクリア
            self._update_page_buttons_state(page_name)
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
            target_page_id = entry_data.get(C.ConfigKey.TARGET, "")
            path_value = self.page_id_to_display.get(target_page_id, target_page_id)
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
        self._update_page_buttons_state(page_name)

    def move_item(self, page_name, direction):
        """選択項目の順序を上下に移動する。"""
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
        self._populate_page_listbox(page_name)
        
        # 選択状態を復元
        listbox.selection_set(new_idx)
        listbox.activate(new_idx)
        self._update_page_buttons_state(page_name)

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
        )
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

    def save_config(self):
        """編集内容を検証して設定ファイルへ保存する。"""
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
            elif key == C.ConfigKey.MENU_ORDER:
                normalized_value = self.MENU_ORDER_DISPLAY_TO_VALUE.get(value, value)
                if normalized_value not in ("normal", "reverse"):
                    messagebox.showerror("入力エラー", f"'{C.ConfigKey.MENU_ORDER}' は 通常 または 逆順 を選択してください。")
                    return
                settings[key] = normalized_value
            elif key == C.ConfigKey.INITIAL_PAGE:
                page_names = set(self.config.get(C.ConfigKey.PAGES, {}).keys())
                normalized_value = self.page_display_to_id.get(value, value)
                if normalized_value not in page_names:
                    messagebox.showerror("入力エラー", f"'{C.ConfigKey.INITIAL_PAGE}' は既存ページから選択してください。")
                    return
                settings[key] = normalized_value
            else:
                settings[key] = value
        self.config[C.ConfigKey.SETTINGS] = settings

        # show_page の遷移先保存
        if hasattr(self, "transition_target_rows"):
            page_names = set(self.config.get(C.ConfigKey.PAGES, {}).keys())
            for row in self.transition_target_rows:
                target_display_or_id = row["target_var"].get()
                target_id = self.page_display_to_id.get(target_display_or_id, target_display_or_id)
                if target_id not in page_names:
                    messagebox.showerror("入力エラー", f"遷移先 '{target_display_or_id}' は既存ページから選択してください。")
                    return
                entry_ref = row.get("entry_ref")
                if entry_ref is not None:
                    entry_ref[C.ConfigKey.TARGET] = target_id

            # 遷移先変更をページ順へ反映してから保存する
            self._recompute_page_order_from_transitions()

        # ページ順の保存（dictの挿入順で保持）
        pages = self.config.get(C.ConfigKey.PAGES, {})
        ordered_page_ids = self._get_page_order_ids()
        reordered_pages = {}
        for page_id in ordered_page_ids:
            if page_id in pages:
                reordered_pages[page_id] = pages[page_id]
        for page_id, page_data in pages.items():
            if page_id not in reordered_pages:
                reordered_pages[page_id] = page_data
        self.config[C.ConfigKey.PAGES] = reordered_pages

        # pagesのmenu_order保存（globalは未設定として扱う）
        for page_name, var in self.page_menu_order_vars.items():
            display_value = var.get()
            value = self.MENU_ORDER_DISPLAY_TO_VALUE.get(display_value, display_value)
            if value not in ("global", "normal", "reverse"):
                messagebox.showerror("入力エラー", f"ページ '{page_name}' の表示順は 全体設定に従う / 通常 / 逆順 のいずれかを選択してください。")
                return

            page_data = self.config.get(C.ConfigKey.PAGES, {}).get(page_name)
            if not page_data:
                continue

            if value == "global":
                page_data.pop(C.ConfigKey.MENU_ORDER, None)
            else:
                page_data[C.ConfigKey.MENU_ORDER] = value

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
