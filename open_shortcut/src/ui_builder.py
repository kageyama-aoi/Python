"""設定に基づくページ/ウィジェット構築を担うモジュール。"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from . import constants as C

class UIBuilder:
    """
    設定に基づいてUIウィジェットを構築するクラス。
    """
    def __init__(self, app, page_container: ttk.Frame, status_label: ttk.Label, settings_button: ttk.Button):
        """
        UIBuilderを初期化する。

        :param app: DirectoryOpenerAppのメインインスタンス。
        :param page_container: メインのページコンテナフレーム。
        :param status_label: ステータス表示ラベル。
        :param settings_button: 設定ボタン。
        """
        self.app = app
        self.master = app.master
        self.config = app.config
        self.action_handler = app.action_handler
        self.style = app.style
        self.icon_images = app.icon_images # icon_imagesはメインアプリで一元管理
        self.dynamic_style_counter = app.dynamic_style_counter

        self.page_container = page_container
        self.status_label = status_label
        self.settings_button = settings_button

    def create_widgets_content(self):
        """UIウィジェットのコンテンツ（ページとボタン）を作成し、既存のコンテナに配置する。"""
        # メインコンテナは既にDirectoryOpenerAppで作成されているため、ここではコンテンツのみを生成する

        pages_config = self.config.get(C.ConfigKey.PAGES)
        if not pages_config or not isinstance(pages_config, dict):
            messagebox.showerror("設定エラー", f"設定ファイルに '{C.ConfigKey.PAGES}' の定義が見つからないか、形式が正しくありません。")
            self.master.destroy()
            return

        for page_name, page_data in pages_config.items():
            frame = ttk.Frame(self.page_container, padding="10")
            self.app.pages[page_name] = frame
            self._populate_page(frame, page_data)

    def _populate_page(self, parent_frame: ttk.Frame, page_data: dict):
        """指定されたフレームにページの内容（ウィジェット）を配置する。"""
        header_text = page_data.get(C.ConfigKey.TITLE, "メニュー")
        header_label = ttk.Label(parent_frame, text=header_text, style="Header.TLabel")
        header_label.pack(pady=(0, 10))

        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        icon_folder = settings.get(C.ConfigKey.ICON_FOLDER, "icons")
        default_icon_name = settings.get(C.ConfigKey.DEFAULT_BUTTON_ICON)

        global_menu_order = settings.get(C.ConfigKey.MENU_ORDER, "normal")
        page_menu_order = page_data.get(C.ConfigKey.MENU_ORDER, "global")
        menu_order = global_menu_order if page_menu_order == "global" else page_menu_order

        entries = list(page_data.get(C.ConfigKey.ENTRIES, []))
        if menu_order == "reverse":
            entries.reverse()

        for entry in entries:
            if not entry.get(C.ConfigKey.ACTIVE, True):
                continue
            
            if entry.get(C.ConfigKey.TYPE) == C.EntryType.SEPARATOR:
                separator = ttk.Separator(parent_frame, orient='horizontal')
                separator.pack(fill='x', pady=10)
            else:
                self._create_button(parent_frame, entry, icon_folder, default_icon_name)

    def _create_button(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """エントリのactionに応じて、適切なUI要素を作成するディスパッチャ。"""
        action = entry.get(C.ConfigKey.ACTION)

        if action in (C.Action.OPEN_DIRECTORY, C.Action.OPEN_URL, C.Action.SHOW_PAGE):
            self._create_simple_action_button(parent, entry, icon_folder, default_icon_name)
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            self._create_parameterized_url_entry(parent, entry, icon_folder, default_icon_name)
        else:
            name = entry.get(C.ConfigKey.NAME, "No Name")
            print(f"情報: ボタン '{name}' には有効なアクションが設定されていません。スキップします。")

    def _create_simple_action_button(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """シンプルなアクション（ディレクトリ/URLを開く、ページ切替）のボタンを作成する。"""
        name = entry.get(C.ConfigKey.NAME, "No Name")
        action = entry.get(C.ConfigKey.ACTION)

        display_name = name
        if action == C.Action.OPEN_DIRECTORY:
            display_name = f"📁 {name}"
        elif action == C.Action.OPEN_URL:
            display_name = f"🌐 {name}"
        elif action == C.Action.SHOW_PAGE:
            display_name = f"→ {name}"

        button_style = "TButton"
        background_color = entry.get(C.ConfigKey.BACKGROUND)
        foreground_color = entry.get(C.ConfigKey.FOREGROUND)

        if background_color or foreground_color:
            self.app.dynamic_style_counter += 1
            button_style = f"Dynamic.{self.app.dynamic_style_counter}.TButton"
            style_options = {"background": background_color, "foreground": foreground_color}
            self.style.configure(button_style, **{k: v for k, v in style_options.items() if v is not None})

        command = None
        if action == C.Action.OPEN_DIRECTORY:
            path = entry.get(C.ConfigKey.PATH)
            if path:
                command = lambda p=path, n=name: self.action_handler.open_directory(p, n)
        elif action == C.Action.SHOW_PAGE:
            target_page = entry.get(C.ConfigKey.TARGET)
            if target_page:
                command = lambda page=target_page: self.action_handler.show_page(page)
        elif action == C.Action.OPEN_URL:
            url = entry.get(C.ConfigKey.URL)
            if url:
                command = lambda u=url, n=name: self.action_handler.open_url(u, n)

        if command is None:
            print(f"情報: ボタン '{name}' には有効なアクションが設定されていません。スキップします。")
            return

        icon_name = entry.get(C.ConfigKey.ICON) or default_icon_name
        button_icon = None
        if icon_name:
            icon_path = os.path.join(icon_folder, icon_name)
            if os.path.exists(icon_path):
                try:
                    image = tk.PhotoImage(file=icon_path)
                    self.icon_images[name] = image
                    button_icon = image
                except tk.TclError:
                    print(f"警告: アイコンを読み込めませんでした: {icon_path}")

        button_instance = ttk.Button(parent, text=display_name, image=button_icon, compound=tk.LEFT, command=command, style=button_style)
        button_instance.pack(fill=tk.X, pady=3)

    def _create_parameterized_url_entry(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """パラメータ付きURLを開くための複合UIを作成する。"""
        name = entry.get(C.ConfigKey.NAME, "No Name")
        base_url = entry.get(C.ConfigKey.BASE_URL)
        parameters_config = entry.get(C.ConfigKey.PARAMETERS, [])

        if not base_url:
            print(f"情報: ボタン '{name}' には base_url が設定されていません。スキップします。")
            return

        display_name = f"⚙️ {name}"
        button_style = "TButton"
        background_color = entry.get(C.ConfigKey.BACKGROUND)
        foreground_color = entry.get(C.ConfigKey.FOREGROUND)

        if background_color or foreground_color:
            self.app.dynamic_style_counter += 1
            button_style = f"Dynamic.{self.app.dynamic_style_counter}.TButton"
            style_options = {"background": background_color, "foreground": foreground_color}
            self.style.configure(button_style, **{k: v for k, v in style_options.items() if v is not None})

        icon_name = entry.get(C.ConfigKey.ICON) or default_icon_name
        button_icon = None
        if icon_name:
            icon_path = os.path.join(icon_folder, icon_name)
            if os.path.exists(icon_path):
                try:
                    image = tk.PhotoImage(file=icon_path)
                    self.icon_images[name] = image
                    button_icon = image
                except tk.TclError:
                    print(f"警告: アイコンを読み込めませんでした: {icon_path}")

        entry_frame = ttk.Frame(parent)
        entry_frame.pack(fill=tk.X, pady=3)

        button_instance = ttk.Button(entry_frame, text=display_name, image=button_icon, compound=tk.LEFT, style=button_style)
        button_instance.pack(side=tk.LEFT, fill=tk.X, expand=False)

        param_vars = {}
        for param_def in parameters_config:
            param_name = param_def.get(C.ConfigKey.NAME)
            param_type = param_def.get(C.ConfigKey.TYPE)
            param_label_text = param_def.get(C.ConfigKey.LABEL, param_name)
            default_value = param_def.get(C.ConfigKey.DEFAULT_VALUE, "")

            if not param_name or not param_type:
                continue

            param_container_frame = ttk.Frame(entry_frame)
            param_container_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

            param_label = ttk.Label(param_container_frame, text=f"{param_label_text}:")
            param_label.pack(side=tk.TOP, anchor=tk.W)

            if param_type == C.ParamType.TEXT:
                param_var = tk.StringVar(value=default_value)
                param_entry = ttk.Entry(param_container_frame, textvariable=param_var, width=20)
                param_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
                param_vars[param_name] = param_var
            elif param_type == C.ParamType.PULLDOWN:
                options = param_def.get(C.ConfigKey.OPTIONS, [])
                param_var = tk.StringVar(value=default_value if default_value in options else (options[0] if options else ""))
                param_combobox = ttk.Combobox(param_container_frame, textvariable=param_var, values=options, state="readonly", width=15)
                param_combobox.pack(side=tk.TOP, fill=tk.X, expand=True)
                param_vars[param_name] = param_var

        command = lambda bu=base_url, pv=param_vars, n=name: self.action_handler.open_parameterized_url(bu, pv, n)
        button_instance.config(command=command)
