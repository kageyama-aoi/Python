import os
from ruamel.yaml import YAML
import config

class ConfigManager:
    """
    設定ファイルの読み書きを担当するクラス。
    ruamel.yamlを使用して、コメントやフォーマットを保持したまま編集を行う。
    """
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        # インデント設定（既存のYAMLに合わせて調整）
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def get_config_file_path(self, mode_key):
        """
        指定されたモードキーに対応する設定ファイルのパスを返す。
        src/config.py でロード時に保存されたメタデータを使用する。
        """
        return config.CONF.get('_meta', {}).get('files', {}).get(mode_key)

    def load_for_edit(self, mode_key):
        """
        編集用に設定ファイルの該当セクションを読み込む。
        
        Args:
            mode_key (str): 's', 'y' などのモード識別子
            
        Returns:
            tuple: (settings_dict, file_path)
            settings_dict は ruamel.yaml の CommentedMap オブジェクト（辞書互換）
        """
        file_path = self.get_config_file_path(mode_key)
        if not file_path or not os.path.exists(file_path):
            return None, None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = self.yaml.load(f)

        # school_specific_defaults -> mode_key のデータを取得
        # ファイル構造に依存するが、現状の設計では school_specific_defaults 下にある前提
        defaults = data.get('school_specific_defaults', {})
        if not defaults:
            return None, file_path
            
        target_data = defaults.get(mode_key)
        return target_data, file_path

    def save_setting(self, mode_key, new_values: dict):
        """
        変更された設定値をファイルに保存し、アプリの設定をリロードする。
        
        Args:
            mode_key (str): モード識別子
            new_values (dict): 更新したいキーと値のペア
        """
        file_path = self.get_config_file_path(mode_key)
        if not file_path:
            raise FileNotFoundError(f"Config file for mode '{mode_key}' not found.")

        # ファイル全体を読み込む（構造とコメントを保持するため）
        with open(file_path, 'r', encoding='utf-8') as f:
            data = self.yaml.load(f)

        # 該当部分を特定
        target_section = data.get('school_specific_defaults', {}).get(mode_key)
        if target_section is None:
             raise KeyError(f"Section '{mode_key}' not found in {file_path}")

        # 値を更新
        for k, v in new_values.items():
            # 改行を含む文字列などは、ruamel.yaml が適切に処理してくれる
            target_section[k] = v

        # ファイルに書き戻す
        with open(file_path, 'w', encoding='utf-8') as f:
            self.yaml.dump(data, f)
            
        # メモリ上のConfigをリロードして最新化
        print(f"Reloading config after update for {mode_key}...")
        config.load_config()
