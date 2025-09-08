import os
import json
import webbrowser
import tkinter as tk
import jsonschema
from tkinter import ttk, messagebox
from .settings_editor import SettingsEditor
from . import constants as C

class DirectoryOpenerApp:
    """
    設定ファイルに基づいてディレクトリやURLを開くボタンを動的に生成する
    Tkinter GUIアプリケーション。
    複数ページの切り替えに対応。
    """
    CONFIG_FILE = os.path.join("data", "config.json")

    def __init__(self, master: tk.Tk):
        """アプリケーションを初期化し、UIを構築する。"""
        self.master = master
        self.icon_images = {}  # PhotoImageオブジェクトを保持 (ガベージコレクション対策)
        self.style = ttk.Style()
        self.dynamic_style_counter = 0
        self.pages = {}

        # 設定ファイルを読み込む
        self.config = self._load_config()
        if not self.config:
            master.destroy()  # 設定がなければウィンドウを閉じる
            return

        self._setup_window()
        self._setup_styles()
        self._create_widgets()

    def _load_config(self) -> dict | None:
        """設定ファイル(JSON)を読み込み、スキーマで検証する。"""
        try:
            # 設定ファイルとスキーマファイルを読み込む
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            schema_path = os.path.join("data", "config.schema.json")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # バリデーションを実行
            jsonschema.validate(instance=config_data, schema=schema)
            
            return config_data

        except FileNotFoundError as e:
            messagebox.showerror("ファイルエラー", f"必要なファイルが見つかりません: {e.filename}")
            return None
        except json.JSONDecodeError:
            messagebox.showerror("JSONエラー", f"設定ファイル '{self.CONFIG_FILE}' の形式が正しくありません。")
            return None
        except jsonschema.ValidationError as e:
            # エラーパスを分かりやすく整形
            error_path = " -> ".join(map(str, e.path)) if e.path else "トップレベル"
            error_message = (
                f"設定ファイル '{self.CONFIG_FILE}' の内容に誤りがあります。\n\n"
                f"エラー内容: {e.message}\n"
                f"場所: {error_path}"
            )
            messagebox.showerror("設定ファイル検証エラー", error_message)
            return None
        except jsonschema.SchemaError as e:
            error_message = (
                f"スキーマファイル '{schema_path}' 自体に誤りがあります。\n\n"
                f"エラー内容: {e.message}"
            )
            messagebox.showerror("スキーマ定義エラー", error_message)
            return None
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの読み込み/検証中に予期せぬエラーが発生しました: {e}")
            return None

    def _setup_window(self):
        """ウィンドウのタイトル、サイズ、アイコンなどを設定する。"""
        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        self.master.title(settings.get(C.ConfigKey.WINDOW_TITLE, "Directory Opener"))
        self.master.geometry(settings.get(C.ConfigKey.GEOMETRY, "400x450"))
        
        resizable = settings.get(C.ConfigKey.RESIZABLE, [False, True])
        self.master.resizable(resizable[0], resizable[1])

        # ウィンドウアイコンの設定
        icon_folder = settings.get(C.ConfigKey.ICON_FOLDER, "icons")
        window_icon = settings.get(C.ConfigKey.WINDOW_ICON)
        if window_icon:
            window_icon_path = os.path.join(icon_folder, window_icon)
            if os.path.exists(window_icon_path):
                try:
                    self.master.iconbitmap(window_icon_path)
                except tk.TclError:
                    print(f"警告: ウィンドウアイコンを読み込めませんでした: {window_icon_path}")

    def _setup_styles(self):
        """ttkウィジェットのスタイルを設定する。"""
        styles_config = self.config.get(C.ConfigKey.STYLES, {})
        for style_name, options in styles_config.items():
            self.style.configure(style_name, **options)

    def _create_widgets(self):
        """UIウィジェットのコンテナを作成し、ページを初期化する。"""
        self.page_container = ttk.Frame(self.master)
        self.page_container.pack(fill=tk.BOTH, expand=True)

        pages_config = self.config.get(C.ConfigKey.PAGES)
        if not pages_config or not isinstance(pages_config, dict):
            messagebox.showerror("設定エラー", f"設定ファイルに '{C.ConfigKey.PAGES}' の定義が見つからないか、形式が正しくありません。")
            self.master.destroy()
            return

        for page_name, page_data in pages_config.items():
            frame = ttk.Frame(self.page_container, padding="10")
            self.pages[page_name] = frame
            self._populate_page(frame, page_data)

        # ステータス表示用のラベル (全ページで共有)
        self.status_label = ttk.Label(self.master, text="準備完了", style="Status.TLabel", anchor=tk.W, padding=(10, 5, 10, 5))
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        # 初期ページを表示
        initial_page = self.config.get(C.ConfigKey.SETTINGS, {}).get(C.ConfigKey.INITIAL_PAGE, "home")
        self.show_page(initial_page)

        # 設定ボタン
        self.settings_button = ttk.Button(self.master, text="設定", command=self.open_settings_window)
        self.settings_button.pack(side=tk.RIGHT, anchor=tk.SE, padx=10, pady=5)

    def _populate_page(self, parent_frame: ttk.Frame, page_data: dict):
        """指定されたフレームにページの内容（ウィジェット）を配置する。"""
        header_text = page_data.get(C.ConfigKey.TITLE, "メニュー")
        header_label = ttk.Label(parent_frame, text=header_text, style="Header.TLabel")
        header_label.pack(pady=(0, 10))

        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        icon_folder = settings.get(C.ConfigKey.ICON_FOLDER, "icons")
        default_icon_name = settings.get(C.ConfigKey.DEFAULT_BUTTON_ICON)

        for entry in page_data.get(C.ConfigKey.ENTRIES, []):
            if entry.get(C.ConfigKey.TYPE) == C.EntryType.SEPARATOR:
                separator = ttk.Separator(parent_frame, orient='horizontal')
                separator.pack(fill='x', pady=10)
            else:
                self._create_button(parent_frame, entry, icon_folder, default_icon_name)

    def _create_button(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """
        エントリのactionに応じて、適切なUI要素を作成するディスパッチャ。
        """
        action = entry.get(C.ConfigKey.ACTION)

        if action in (C.Action.OPEN_DIRECTORY, C.Action.OPEN_URL, C.Action.SHOW_PAGE):
            self._create_simple_action_button(parent, entry, icon_folder, default_icon_name)
        elif action == C.Action.OPEN_PARAMETERIZED_URL:
            self._create_parameterized_url_entry(parent, entry, icon_folder, default_icon_name)
        else:
            # Handle unknown or missing action
            name = entry.get(C.ConfigKey.NAME, "No Name")
            print(f"情報: ボタン '{name}' には有効なアクションが設定されていません。スキップします。")

    def _create_simple_action_button(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """シンプルなアクション（ディレクトリ/URLを開く、ページ切替）のボタンを作成する。"""
        name = entry.get(C.ConfigKey.NAME, "No Name")
        action = entry.get(C.ConfigKey.ACTION)

        # アクションに応じてボタン名にアイコンを追加
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
            self.dynamic_style_counter += 1
            button_style = f"Dynamic.{self.dynamic_style_counter}.TButton"
            style_options = {"background": background_color, "foreground": foreground_color}
            self.style.configure(button_style, **{k: v for k, v in style_options.items() if v is not None})

        command = None
        if action == C.Action.OPEN_DIRECTORY:
            path = entry.get(C.ConfigKey.PATH)
            if path:
                command = lambda p=path, n=name: self.open_directory(p, n)
        elif action == C.Action.SHOW_PAGE:
            target_page = entry.get(C.ConfigKey.TARGET)
            if target_page:
                command = lambda page=target_page: self.show_page(page)
        elif action == C.Action.OPEN_URL:
            url = entry.get(C.ConfigKey.URL)
            if url:
                command = lambda u=url, n=name: self.open_url(u, n)

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
                    self.icon_images[name] = image # Store reference
                    button_icon = image
                except tk.TclError:
                    print(f"警告: アイコンを読み込めませんでした: {icon_path}")

        button_instance = ttk.Button(
            parent,
            text=display_name,
            image=button_icon,
            compound=tk.LEFT,
            command=command,
            style=button_style
        )
        button_instance.pack(fill=tk.X, pady=3)

    def _create_parameterized_url_entry(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """パラメータ付きURLを開くための複合UI（ボタン＋入力欄）を作成する。"""
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
            self.dynamic_style_counter += 1
            button_style = f"Dynamic.{self.dynamic_style_counter}.TButton"
            style_options = {"background": background_color, "foreground": foreground_color}
            self.style.configure(button_style, **{k: v for k, v in style_options.items() if v is not None})

        icon_name = entry.get(C.ConfigKey.ICON) or default_icon_name
        button_icon = None
        if icon_name:
            icon_path = os.path.join(icon_folder, icon_name)
            if os.path.exists(icon_path):
                try:
                    image = tk.PhotoImage(file=icon_path)
                    self.icon_images[name] = image # Store reference
                    button_icon = image
                except tk.TclError:
                    print(f"警告: アイコンを読み込めませんでした: {icon_path}")

        # Create a frame to hold the button and its parameters
        entry_frame = ttk.Frame(parent)
        entry_frame.pack(fill=tk.X, pady=3)

        # Create the button within this new frame
        button_instance = ttk.Button(
            entry_frame,
            text=display_name,
            image=button_icon,
            compound=tk.LEFT,
            style=button_style
        )
        button_instance.pack(side=tk.LEFT, fill=tk.X, expand=False)

        param_vars = {}
        for param_def in parameters_config:
            param_name = param_def.get(C.ConfigKey.NAME)
            param_type = param_def.get(C.ConfigKey.TYPE)
            param_label_text = param_def.get(C.ConfigKey.LABEL, param_name)
            default_value = param_def.get(C.ConfigKey.DEFAULT_VALUE, "")

            if not param_name or not param_type:
                print(f"警告: 不完全なパラメータ定義が検出されました: {param_def}。スキップします。")
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
            else:
                print(f"警告: 未知のパラメータタイプ '{param_type}' が検出されました。スキップします。")
                continue

        command = lambda bu=base_url, pv=param_vars, n=name: self._open_parameterized_url(bu, pv, n)
        button_instance.config(command=command)

    def reload_ui(self):
        """UIを破棄し、設定を再読み込みして再構築する。"""
        # 1. Destroy all dynamic widgets
        for widget in self.master.winfo_children():
            widget.destroy()

        # 2. Reset internal state
        self.icon_images = {}
        self.dynamic_style_counter = 0
        self.pages = {}

        # 3. Reload config
        self.config = self._load_config()
        if not self.config:
            self.master.destroy()
            return

        # 4. Re-create UI
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        print("UI reloaded successfully.")

    def show_page(self, page_name: str):
        """指定された名前のページを表示し、ウィンドウタイトルを更新する。"""
        page = self.pages.get(page_name)
        if page:
            for p in self.pages.values():
                p.pack_forget()
            page.pack(fill=tk.BOTH, expand=True)
            
            # ページのタイトルか、なければグローバルなタイトルを設定
            page_title = self.config.get(C.ConfigKey.PAGES, {}).get(page_name, {}).get(C.ConfigKey.WINDOW_TITLE)
            global_title = self.config.get(C.ConfigKey.SETTINGS, {}).get(C.ConfigKey.WINDOW_TITLE, "Directory Opener")
            self.master.title(page_title or global_title)
            
            self.status_label.config(text=f"「{page_name}」ページを表示しました。")
        else:
            messagebox.showwarning("警告", f"ページ '{page_name}' が見つかりません。")
            self.status_label.config(text=f"エラー: ページ '{page_name}' の表示に失敗しました。")

    def open_directory(self, path: str, name: str):
        """指定されたパスをエクスプローラーで開く。"""
        try:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                os.startfile(expanded_path)
                message = f"「{name}」を開きました。"
                self.status_label.config(foreground="blue")
            else:
                message = f"エラー: パスが見つかりません - {expanded_path}"
                self.status_label.config(foreground="red")
        except Exception as e:
            message = f"エラー: {e}"
            self.status_label.config(foreground="red")

        self.status_label.config(text=message)

    def open_url(self, url: str, name: str):
        """指定されたURLをデフォルトのブラウザで開く。"""
        try:
            webbrowser.open_new_tab(url)
            message = f"URL「{name}」をブラウザで開きました。"
            self.status_label.config(foreground="blue")
        except Exception as e:
            message = f"URLを開けませんでした: {e}"
            self.status_label.config(foreground="red")
        
        self.status_label.config(text=message)

    def _open_parameterized_url(self, base_url: str, param_vars: dict, name: str):
        """
        パラメータをURLパスに埋め込み、ブラウザで開く。
        param_varsは、パラメータ名とtk.StringVarオブジェクトの辞書。
        """
        try:
            # パラメータ値を収集し、URLエンコードする
            replacements = {}
            for param_name, param_var in param_vars.items():
                value = param_var.get()
                # URLパスに埋め込むため、個々の値もURLエンコードする
                replacements[param_name] = webbrowser.urlquote(value)

            # base_url内のプレースホルダーを置換する
            # 例: https://example.com/{param1}/{param2} -> https://example.com/value1/value2
            # 未指定のパラメータは空文字列で置換される
            full_url = base_url.format(**replacements)

            webbrowser.open_new_tab(full_url)
            message = f"パラメータ付きURL「{name}」をブラウザで開きました: {full_url}"
            self.status_label.config(foreground="blue")
        except KeyError as e:
            message = f"エラー: URLのプレースホルダー '{e}' に対応するパラメータが見つかりません。"
            self.status_label.config(foreground="red")
        except Exception as e:
            message = f"パラメータ付きURLを開けませんでした: {e}"
            self.status_label.config(foreground="red")

        self.status_label.config(text=message)

    def open_settings_window(self):
        """設定画面を新しいウィンドウで開く。"""
        settings_window = SettingsEditor(self.master, on_save_callback=self.reload_ui)
        settings_window.grab_set() # モーダルウィンドウにする

def main():
    """アプリケーションを起動する。"""
    root = tk.Tk()
    app = DirectoryOpenerApp(root)
    if root.winfo_exists():
        root.mainloop()

if __name__ == "__main__":
    main()
