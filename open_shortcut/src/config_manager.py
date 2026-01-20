"""設定ファイルの読み込み・検証・保存を担うモジュール。"""

import os
import json
import jsonschema
from tkinter import messagebox

class ConfigManager:
    """
    設定ファイル(config.json)の読み込み、検証、アクセスを管理するクラス。
    """
    def __init__(self, config_path="data/config.json", schema_path="data/config.schema.json"):
        """
        ConfigManagerを初期化し、設定を読み込んで検証する。
        :param config_path: 設定ファイルのパス。
        :param schema_path: スキーマファイルのパス。
        """
        self.config_path = config_path
        self.schema_path = schema_path
        self.config = self.load_and_validate_config()

    def load_and_validate_config(self) -> dict | None:
        """
        設定ファイル(JSON)を読み込み、スキーマで検証する。
        成功した場合は設定データを、失敗した場合はNoneを返す。
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            jsonschema.validate(instance=config_data, schema=schema)
            
            return config_data

        except FileNotFoundError as e:
            messagebox.showerror("ファイルエラー", f"必要なファイルが見つかりません: {e.filename}")
            return None
        except json.JSONDecodeError:
            messagebox.showerror("JSONエラー", f"設定ファイル '{self.config_path}' の形式が正しくありません。")
            return None
        except jsonschema.ValidationError as e:
            error_path = " -> ".join(map(str, e.path)) if e.path else "トップレベル"
            error_message = (
                f"設定ファイル '{self.config_path}' の内容に誤りがあります。\n\n"
                f"エラー内容: {e.message}\n"
                f"場所: {error_path}"
            )
            messagebox.showerror("設定ファイル検証エラー", error_message)
            return None
        except jsonschema.SchemaError as e:
            error_message = (
                f"スキーマファイル '{self.schema_path}' 自体に誤りがあります。\n\n"
                f"エラー内容: {e.message}"
            )
            messagebox.showerror("スキーマ定義エラー", error_message)
            return None
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの読み込み/検証中に予期せぬエラーが発生しました: {e}")
            return None

    def get_config(self) -> dict | None:
        """
        検証済みの設定データを返す。
        """
        return self.config

    def reload(self) -> bool:
        """
        設定を再読み込みし、検証する。
        成功した場合はTrueを、失敗した場合はFalseを返す。
        """
        new_config = self.load_and_validate_config()
        if new_config is not None:
            self.config = new_config
            return True
        return False

    def save_config(self, new_config: dict) -> bool:
        """
        新しい設定を検証し、ファイルに保存する。
        :param new_config: 保存する新しい設定データ。
        :return: 保存に成功した場合はTrue、失敗した場合はFalse。
        """
        try:
            # スキーマを読み込んで新しい設定を検証する
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            jsonschema.validate(instance=new_config, schema=schema)

            # 検証が成功したらファイルに書き込む
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            
            # メモリ上の設定も更新
            self.config = new_config
            return True

        except jsonschema.ValidationError as e:
            error_path = " -> ".join(map(str, e.path)) if e.path else "トップレベル"
            error_message = (
                f"保存しようとした設定内容に誤りがあります。\n\n"
                f"エラー内容: {e.message}\n"
                f"場所: {error_path}"
            )
            messagebox.showerror("設定検証エラー", error_message)
            return False
        except Exception as e:
            messagebox.showerror("保存エラー", f"設定の保存中にエラーが発生しました: {e}")
            return False
