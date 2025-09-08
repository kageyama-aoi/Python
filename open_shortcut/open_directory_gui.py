import os
import json
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from settings_editor import SettingsEditor

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
        """設定ファイル(JSON)を読み込む。"""
        try:
            # スクリプトと同じディレクトリにある設定ファイルを開く
            script_dir = os.path.dirname(__file__)
            config_path = os.path.join(script_dir, self.CONFIG_FILE)
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("エラー", f"設定ファイルが見つかりません: {self.CONFIG_FILE}")
            return None
        except json.JSONDecodeError:
            messagebox.showerror("エラー", f"設定ファイル '{self.CONFIG_FILE}' の形式が正しくありません。")
            return None
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの読み込み中に予期せぬエラーが発生しました: {e}")
            return None

    def _setup_window(self):
        """ウィンドウのタイトル、サイズ、アイコンなどを設定する。"""
        settings = self.config.get("settings", {})
        self.master.title(settings.get("window_title", "Directory Opener"))
        self.master.geometry(settings.get("geometry", "400x450"))
        
        resizable = settings.get("resizable", [False, True])
        self.master.resizable(resizable[0], resizable[1])

        # ウィンドウアイコンの設定
        icon_folder = settings.get("icon_folder", "icons")
        window_icon = settings.get("window_icon")
        if window_icon:
            window_icon_path = os.path.join(os.path.dirname(__file__), icon_folder, window_icon)
            if os.path.exists(window_icon_path):
                try:
                    self.master.iconbitmap(window_icon_path)
                except tk.TclError:
                    print(f"警告: ウィンドウアイコンを読み込めませんでした: {window_icon_path}")

    def _setup_styles(self):
        """ttkウィジェットのスタイルを設定する。"""
        styles_config = self.config.get("styles", {})
        for style_name, options in styles_config.items():
            self.style.configure(style_name, **options)

    def _create_widgets(self):
        """UIウィジェットのコンテナを作成し、ページを初期化する。"""
        self.page_container = ttk.Frame(self.master)
        self.page_container.pack(fill=tk.BOTH, expand=True)

        pages_config = self.config.get("pages")
        if not pages_config or not isinstance(pages_config, dict):
            messagebox.showerror("設定エラー", "設定ファイルに 'pages' の定義が見つからないか、形式が正しくありません。")
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
        initial_page = self.config.get("settings", {}).get("initial_page", "home")
        self.show_page(initial_page)

        # 設定ボタン
        settings_button = ttk.Button(self.master, text="設定", command=self.open_settings_window)
        settings_button.pack(side=tk.RIGHT, anchor=tk.SE, padx=10, pady=5)

    def _populate_page(self, parent_frame: ttk.Frame, page_data: dict):
        """指定されたフレームにページの内容（ウィジェット）を配置する。"""
        header_text = page_data.get("title", "メニュー")
        header_label = ttk.Label(parent_frame, text=header_text, style="Header.TLabel")
        header_label.pack(pady=(0, 10))

        settings = self.config.get("settings", {})
        icon_folder = settings.get("icon_folder", "icons")
        default_icon_name = settings.get("default_button_icon")

        for entry in page_data.get("entries", []):
            if entry.get("type") == "separator":
                separator = ttk.Separator(parent_frame, orient='horizontal')
                separator.pack(fill='x', pady=10)
            else:
                self._create_button(parent_frame, entry, icon_folder, default_icon_name)

    def _create_button(self, parent: ttk.Frame, entry: dict, icon_folder: str, default_icon_name: str | None):
        """設定情報から一つのボタンを作成する。"""
        name = entry.get("name", "No Name")
        action = entry.get("action", "open_directory")

        # アクションに応じてボタン名にアイコンを追加
        display_name = name
        if action == "open_directory":
            display_name = f"📁 {name}"
        elif action == "open_url":
            display_name = f"🌐 {name}"
        elif action == "show_page":
            display_name = f"→ {name}"
        elif action == "open_parameterized_url": # NEW
            display_name = f"⚙️ {name}" # Special icon for parameterized URL

        button_style = "TButton"
        background_color = entry.get("background")
        foreground_color = entry.get("foreground")

        if background_color or foreground_color:
            self.dynamic_style_counter += 1
            button_style = f"Dynamic.{self.dynamic_style_counter}.TButton"
            style_options = {"background": background_color, "foreground": foreground_color}
            self.style.configure(button_style, **{k: v for k, v in style_options.items() if v is not None})

        command = None
        button_instance = None # To hold the button widget, as it might be created in different branches

        icon_name = entry.get("icon") or default_icon_name
        button_icon = None
        if icon_name:
            icon_path = os.path.join(os.path.dirname(__file__), icon_folder, icon_name)
            if os.path.exists(icon_path):
                try:
                    image = tk.PhotoImage(file=icon_path)
                    self.icon_images[name] = image # Store reference to prevent garbage collection
                    button_icon = image
                except tk.TclError:
                    print(f"警告: アイコンを読み込めませんでした: {icon_path}")

        if action == "open_directory":
            path = entry.get("path")
            if path:
                command = lambda p=path, n=name: self.open_directory(p, n)
        elif action == "show_page":
            target_page = entry.get("target")
            if target_page:
                command = lambda page=target_page: self.show_page(page)
        elif action == "open_url":
            url = entry.get("url")
            if url:
                command = lambda u=url, n=name: self.open_url(u, n)
        elif action == "open_parameterized_url":
            base_url = entry.get("base_url")
            parameters_config = entry.get("parameters", [])
            if base_url and parameters_config is not None:
                # Create a frame to hold the button and its parameters
                entry_frame = ttk.Frame(parent)
                entry_frame.pack(fill=tk.X, pady=3) # Pack the container frame

                # Create the button within this new frame
                button_instance = ttk.Button(
                    entry_frame, # Parent is now entry_frame
                    text=display_name,
                    image=button_icon,
                    compound=tk.LEFT,
                    style=button_style
                )
                button_instance.pack(side=tk.LEFT, fill=tk.X, expand=False) # Pack button to the left, don't expand

                param_vars = {} # Dictionary to store parameter StringVar objects by name
                for param_def in parameters_config:
                    param_name = param_def.get("name")
                    param_type = param_def.get("type")
                    param_label_text = param_def.get("label", param_name)
                    default_value = param_def.get("default_value", "")

                    if not param_name or not param_type:
                        print(f"警告: 不完全なパラメータ定義が検出されました: {param_def}。スキップします。")
                        continue

                    # Create a sub-frame for each parameter to control layout better
                    param_container_frame = ttk.Frame(entry_frame)
                    param_container_frame.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

                    param_label = ttk.Label(param_container_frame, text=f"{param_label_text}:")
                    param_label.pack(side=tk.TOP, anchor=tk.W) # Label above input

                    if param_type == "text":
                        param_var = tk.StringVar(value=default_value)
                        param_entry = ttk.Entry(param_container_frame, textvariable=param_var, width=20)
                        param_entry.pack(side=tk.TOP, fill=tk.X, expand=True)
                        param_vars[param_name] = param_var # Store StringVar
                    elif param_type == "pulldown":
                        options = param_def.get("options", [])
                        param_var = tk.StringVar(value=default_value if default_value in options else (options[0] if options else ""))
                        param_combobox = ttk.Combobox(param_container_frame, textvariable=param_var, values=options, state="readonly", width=15)
                        param_combobox.pack(side=tk.TOP, fill=tk.X, expand=True)
                        param_vars[param_name] = param_var # Store StringVar
                    else:
                        print(f"警告: 未知のパラメータタイプ '{param_type}' が検出されました。スキップします。")
                        continue

                # Set the command for the button after all widgets are created
                command = lambda bu=base_url, pv=param_vars, n=name: self._open_parameterized_url(bu, pv, n)
                button_instance.config(command=command) # Configure the command for the button
                return # Exit the function as this entry is fully handled

        if command is None:
            print(f"情報: ボタン '{name}' には有効なアクションが設定されていません。スキップします。")
            return

        # Common button creation for other actions
        button_instance = ttk.Button(
            parent,
            text=display_name,
            image=button_icon,
            compound=tk.LEFT,
            command=command,
            style=button_style
        )
        button_instance.pack(fill=tk.X, pady=3)

    def show_page(self, page_name: str):
        """指定された名前のページを表示し、ウィンドウタイトルを更新する。"""
        page = self.pages.get(page_name)
        if page:
            for p in self.pages.values():
                p.pack_forget()
            page.pack(fill=tk.BOTH, expand=True)
            
            # ページのタイトルか、なければグローバルなタイトルを設定
            page_title = self.config.get("pages", {}).get(page_name, {}).get("window_title")
            global_title = self.config.get("settings", {}).get("window_title", "Directory Opener")
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
        settings_window = SettingsEditor(self.master)
        settings_window.grab_set() # モーダルウィンドウにする

def main():
    """アプリケーションを起動する。"""
    root = tk.Tk()
    app = DirectoryOpenerApp(root)
    if root.winfo_exists():
        root.mainloop()

if __name__ == "__main__":
    main()
