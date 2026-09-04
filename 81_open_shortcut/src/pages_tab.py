"""ページ編集タブ（ページ一覧・項目の並べ替え・表示/非表示切り替え）。

SettingsEditor に組み込むミックスイン。self.config / self.pages_widgets /
右ペインのフォーム（button_form.py）と連携する。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from . import constants as C


class PagesTabMixin:
    """ページ編集タブとリスト操作を提供する。"""

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
            pages_notebook.add(list_frame, text=self._format_page_tab_short_label(page_name, page_data))
            self.page_frame_to_name[list_frame] = page_name
            self.page_name_to_frame[page_name] = list_frame

            # ページごとのメニュー表示順
            page_order_frame = ttk.Frame(list_frame)
            page_order_frame.pack(fill="x", pady=2)

            ttk.Label(page_order_frame, text="表示順:").pack(side="left", padx=2)
            page_menu_order = page_data.get(C.ConfigKey.MENU_ORDER, C.MenuOrder.GLOBAL.value)
            if page_menu_order not in (C.MenuOrder.GLOBAL, C.MenuOrder.NORMAL, C.MenuOrder.REVERSE):
                page_menu_order = C.MenuOrder.GLOBAL.value

            page_menu_order_var = tk.StringVar(value=C.MENU_ORDER_VALUE_TO_DISPLAY[page_menu_order])
            self.page_menu_order_vars[page_name] = page_menu_order_var

            page_order_combo = ttk.Combobox(
                page_order_frame,
                textvariable=page_menu_order_var,
                values=["全体設定に従う", "通常", "逆順"],
                state="readonly",
                width=14,  # 「全体設定に従う」が収まる幅
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

        # 右ペインはadd()時点では空で要求サイズがほぼ0のため、sashが左に寄ったまま
        # 固定されてしまう。フォーム構築後にウィンドウ幅の半分へ明示的に置き直す。
        def _center_sash():
            if not paned_window.winfo_exists():
                return
            paned_window.update_idletasks()
            width = paned_window.winfo_width()
            if width > 1:
                # 左ペイン（ページ一覧・タブ）をやや広めに。右のフォームは
                # 入力欄が収まる幅（約380px）を確保する。
                left = min(int(width * 0.55), max(width - 380, width // 2))
                paned_window.sashpos(0, left)
        parent.after(50, _center_sash)

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

        if not self.confirm_discard_form():
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

        if not self.confirm_discard_form():
            return
        entries[idx][C.ConfigKey.ACTIVE] = True
        self._populate_page_listbox(page_name)
        self.clear_button_form()
        self._set_status(f"項目「{entries[idx].get(C.ConfigKey.NAME, '(無名)')}」を表示しました。")

    def add_button(self, page_name):
        """新規追加モードに切り替える。"""
        if not self.confirm_discard_form():
            return
        # 選択を解除して追加モードにする
        listbox = self.pages_widgets[page_name]["listbox"]
        listbox.selection_clear(0, tk.END)
        self.clear_button_form()
        self._form_page = page_name
        self._update_page_buttons_state(page_name)

    def on_listbox_select(self, event, page_name):
        """リストボックス選択に応じてフォームへ値を反映する。"""
        listbox = event.widget
        selected_indices = listbox.curselection()
        new_ref = (page_name, selected_indices[0]) if selected_indices else None

        # 同じ項目への再通知は無視（無駄なフォーム再描画・確認を避ける）
        if new_ref == getattr(self, "_loaded_ref", None):
            self._update_page_buttons_state(page_name)
            return

        # 未保存の入力がある状態で別項目へ移ろうとしたら確認する
        if not self.confirm_discard_form():
            listbox.selection_clear(0, tk.END)
            prev = getattr(self, "_loaded_ref", None)
            if prev and prev[0] == page_name and prev[1] < listbox.size():
                listbox.selection_set(prev[1])
            return

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
        self._form_page = page_name
        self._loaded_ref = new_ref
        self._reset_form_dirty()  # 読み込んだ直後は未保存ではない
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

        # フォームに読み込み中の項目が動いたら参照インデックスを追従させる
        loaded = getattr(self, "_loaded_ref", None)
        if loaded and loaded[0] == page_name:
            if loaded[1] == idx:
                self._loaded_ref = (page_name, new_idx)
            elif loaded[1] == new_idx:
                self._loaded_ref = (page_name, idx)

        # リストボックスの表示を更新
        self._populate_page_listbox(page_name)

        # 選択状態を復元
        listbox.selection_set(new_idx)
        listbox.activate(new_idx)
        self._update_page_buttons_state(page_name)
