"""ディレクトリ/URL操作やページ遷移のアクション処理をまとめたモジュール。"""

import os
import webbrowser
from tkinter import messagebox
from . import constants as C

class ActionHandler:
    """
    アプリケーションのアクション（ディレクトリを開く、URLを開くなど）を処理するクラス。
    """
    def __init__(self, app):
        """
        ActionHandlerを初期化する。

        :param app: DirectoryOpenerAppのメインインスタンス。
                    ステータスラベルやページ切り替えメソッドへのアクセスに利用。
        """
        self.app = app

    def open_directory(self, path: str, name: str):
        """指定されたパスをエクスプローラーで開く。"""
        try:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                os.startfile(expanded_path)
                message = f"「{name}」を開きました。"
                self.app.status_label.config(foreground="blue")
            else:
                message = f"エラー: パスが見つかりません - {expanded_path}"
                self.app.status_label.config(foreground="red")
        except Exception as e:
            message = f"エラー: {e}"
            self.app.status_label.config(foreground="red")

        self.app.status_label.config(text=message)

    def open_url(self, url: str, name: str):
        """指定されたURLをデフォルトのブラウザで開く。"""
        try:
            webbrowser.open_new_tab(url)
            message = f"URL「{name}」をブラウザで開きました。"
            self.app.status_label.config(foreground="blue")
        except Exception as e:
            message = f"URLを開けませんでした: {e}"
            self.app.status_label.config(foreground="red")
        
        self.app.status_label.config(text=message)

    def open_parameterized_url(self, base_url: str, param_vars: dict, name: str):
        """
        パラメータをURLパスに埋め込み、ブラウザで開く。
        param_varsは、パラメータ名とtk.StringVarオブジェクトの辞書。
        """
        try:
            # パラメータ値を収集する
            replacements = {param_name: param_var.get() for param_name, param_var in param_vars.items()}

            # base_url内のプレースホルダーを置換する
            full_url = base_url.format(**replacements)

            webbrowser.open_new_tab(full_url)
            message = f"パラメータ付きURL「{name}」をブラウザで開きました: {full_url}"
            self.app.status_label.config(foreground="blue")
        except KeyError as e:
            message = f"エラー: URLのプレースホルダー '{e}' に対応するパラメータが見つかりません。"
            self.app.status_label.config(foreground="red")
        except Exception as e:
            message = f"パラメータ付きURLを開けませんでした: {e}"
            self.app.status_label.config(foreground="red")

        self.app.status_label.config(text=message)

    def show_page(self, page_name: str):
        """指定されたページを表示するようメインアプリに要求する。"""
        self.app.show_page(page_name)
