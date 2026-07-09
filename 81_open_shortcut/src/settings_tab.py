"""基本設定タブ（ウィンドウ設定・初期ページ・ページ遷移先・ページ順の自動計算）。

SettingsEditor に組み込むミックスイン。self.config / self.page_display_to_id /
self.pages_widgets 等の共有状態は settings_editor.py 側で初期化される。
"""

import tkinter as tk
from tkinter import ttk
from . import constants as C


class SettingsTabMixin:
    """基本設定タブとページ順同期ロジックを提供する。"""

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
            state="readonly",
            justify="right",
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
            state="readonly",
            justify="right",
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
                target_combo = ttk.Combobox(
                    row,
                    textvariable=target_var,
                    values=page_display_names,
                    state="readonly",
                    justify="right",
                )
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
