"""設定に基づくページ/ウィジェット構築を担うモジュール。"""

import logging
import os
import tkinter as tk
from tkinter import ttk, messagebox
from . import constants as C

logger = logging.getLogger(__name__)

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
        self.icon_images = app.icon_images # icon_imagesはメインアプリで一元管理（同一辞書を共有）

        # 色ペア(bg, fg) -> ttkスタイル名 のメモ。ボタン1個ごとに採番せず、
        # 同じ色は使い回し、リロードでも作り直さない（#152）。
        self._colored_button_styles: dict[tuple[str, str], str] = {}

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

        global_menu_order = settings.get(C.ConfigKey.MENU_ORDER, C.MenuOrder.NORMAL.value)
        page_menu_order = page_data.get(C.ConfigKey.MENU_ORDER, C.MenuOrder.GLOBAL.value)
        menu_order = global_menu_order if page_menu_order == C.MenuOrder.GLOBAL else page_menu_order

        entries = list(page_data.get(C.ConfigKey.ENTRIES, []))
        if menu_order == C.MenuOrder.REVERSE:
            entries.reverse()

        for entry in entries:
            if not entry.get(C.ConfigKey.ACTIVE, True):
                continue
            
            if entry.get(C.ConfigKey.TYPE) == C.EntryType.SEPARATOR:
                separator = ttk.Separator(parent_frame, orient='horizontal')
                separator.pack(fill='x', pady=10)
            else:
                self._create_button(parent_frame, entry, icon_folder, default_icon_name)

    def _colored_button_style(self, background: str | None, foreground: str | None) -> str | None:
        """背景色/文字色の組み合わせごとに一意なttkスタイル名を返す。

        同じ色ペアは同じスタイルを使い回し、リロード後も作り直さない。
        色指定が無ければ None を返す（呼び出し側で既定スタイルを選ぶ）。

        注: sv_ttk（ダークテーマ）導入時はボタンが画像ベースのため background は
        反映されず、foreground（文字色）のみ効く。詳細は README「styles」参照（#151）。
        """
        bg = (background or "").strip()
        fg = (foreground or "").strip()
        if not bg and not fg:
            return None

        key = (bg.lower(), fg.lower())
        style_name = self._colored_button_styles.get(key)
        if style_name is None:
            style_name = f"Colored{len(self._colored_button_styles)}.TButton"
            options = {}
            if bg:
                options["background"] = bg
            if fg:
                options["foreground"] = fg
            self.style.configure(style_name, **options)
            self._colored_button_styles[key] = style_name
        return style_name

    def _load_icon(self, icon_folder: str, icon_name: str | None, name: str) -> tk.PhotoImage | None:
        """アイコン画像を読み込んで返す。

        GC でボタンから画像が消えないよう self.icon_images に参照を保持する。
        未指定・ファイル無し・読み込み失敗時は None（呼び出し側はアイコン無しで続行）。
        """
        if not icon_name:
            return None
        icon_path = os.path.join(icon_folder, icon_name)
        if not os.path.exists(icon_path):
            return None
        try:
            image = tk.PhotoImage(file=icon_path)
        except tk.TclError:
            logger.warning("アイコン読込失敗: %s", icon_path)
            return None
        self.icon_images[name] = image
        return image

    def _create_button(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """エントリのactionに応じて、適切なUI要素を作成するディスパッチャ。"""
        action = entry.get(C.ConfigKey.ACTION)

        if action in (C.Action.OPEN_DIRECTORY, C.Action.OPEN_URL, C.Action.SHOW_PAGE):
            self._create_simple_action_button(parent, entry, icon_folder, default_icon_name)
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            self._create_parameterized_url_entry(parent, entry, icon_folder, default_icon_name)
        else:
            name = entry.get(C.ConfigKey.NAME, "No Name")
            logger.warning("ボタン省略: 未対応のアクション '%s' - %s", action, name)

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

        # 明示的な色指定は最優先（既存の個別カスタマイズを壊さない）
        button_style = self._colored_button_style(
            entry.get(C.ConfigKey.BACKGROUND), entry.get(C.ConfigKey.FOREGROUND)
        )
        if button_style is None:
            if action == C.Action.SHOW_PAGE:
                # ページ遷移ボタンは色指定なしでも自動でNavスタイル（styles.Nav.TButton）が乗る
                button_style = "Nav.TButton"
            else:
                button_style = "TButton"

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
            logger.warning("ボタン省略: パス/URL/遷移先が未設定 - %s", name)
            return

        button_icon = self._load_icon(icon_folder, entry.get(C.ConfigKey.ICON) or default_icon_name, name)

        button_instance = ttk.Button(parent, text=display_name, image=button_icon, compound=tk.LEFT, command=command, style=button_style)
        button_instance.pack(fill=tk.X, pady=3)

    def _create_parameterized_url_entry(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """パラメータ付きURLを開くための複合UIを作成する。"""
        name = entry.get(C.ConfigKey.NAME, "No Name")
        base_url = entry.get(C.ConfigKey.BASE_URL)
        parameters_config = entry.get(C.ConfigKey.PARAMETERS, [])

        if not base_url:
            logger.warning("ボタン省略: base_url未設定 - %s", name)
            return

        display_name = f"⚙️ {name}"
        button_style = self._colored_button_style(
            entry.get(C.ConfigKey.BACKGROUND), entry.get(C.ConfigKey.FOREGROUND)
        ) or "TButton"

        button_icon = self._load_icon(icon_folder, entry.get(C.ConfigKey.ICON) or default_icon_name, name)

        entry_frame = ttk.Frame(parent)
        entry_frame.pack(fill=tk.X, pady=3)

        # ボタンを上、パラメータ入力を下にインデントして縦積みする。
        # 横並びだと狭いウィンドウやパラメータ複数で右にはみ出すため（#154）。
        button_instance = ttk.Button(entry_frame, text=display_name, image=button_icon, compound=tk.LEFT, style=button_style)
        button_instance.pack(side=tk.TOP, fill=tk.X)

        params_frame = ttk.Frame(entry_frame)
        if parameters_config:
            params_frame.pack(side=tk.TOP, fill=tk.X, padx=(16, 0), pady=(2, 0))

        param_vars = {}
        for param_def in parameters_config:
            param_name = param_def.get(C.ConfigKey.NAME)
            param_type = param_def.get(C.ConfigKey.TYPE)
            param_label_text = param_def.get(C.ConfigKey.LABEL, param_name)
            default_value = param_def.get(C.ConfigKey.DEFAULT_VALUE, "")

            if not param_name or not param_type:
                continue

            param_container_frame = ttk.Frame(params_frame)
            param_container_frame.pack(side=tk.TOP, fill=tk.X, pady=1)

            param_label = ttk.Label(param_container_frame, text=f"{param_label_text}:")
            param_label.pack(side=tk.LEFT, anchor=tk.W, padx=(0, 4))

            if param_type == C.ParamType.TEXT:
                param_var = tk.StringVar(value=default_value)
                param_entry = ttk.Entry(param_container_frame, textvariable=param_var)
                param_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                param_vars[param_name] = param_var
            elif param_type == C.ParamType.PULLDOWN:
                options = param_def.get(C.ConfigKey.OPTIONS, [])
                param_var = tk.StringVar(value=default_value if default_value in options else (options[0] if options else ""))
                param_combobox = ttk.Combobox(param_container_frame, textvariable=param_var, values=options, state="readonly")
                param_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
                param_vars[param_name] = param_var

        command = lambda bu=base_url, pv=param_vars, n=name: self.action_handler.open_parameterized_url(bu, pv, n)
        button_instance.config(command=command)
