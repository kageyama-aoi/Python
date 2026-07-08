import os
from ruamel.yaml import YAML
from config import config


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
        src/config/config.py でロード時に保存されたメタデータを使用する。
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

    def add_pattern(self, key: str, label: str, requires_environment: bool, fields: dict):
        """
        新しいTRパターンを追加する。
        - main.yaml の menus.tr_options に新エントリを追記
        - config/modes/task_report/{key}.yaml を新規作成

        Args:
            key (str): パターン識別子（半角英数字）
            label (str): GUI表示名
            requires_environment (bool): 環境選択が必要か
            fields (dict): フィールド値 (Schools, Project, Title, Comments など)

        Raises:
            ValueError: キーが既に存在する場合
        """
        # 重複チェック
        existing_keys = [opt['key'] for opt in config.CONF.get('menus', {}).get('tr_options', [])]
        if key in existing_keys:
            raise ValueError(f"キー '{key}' は既に存在します。")

        # 1. main.yaml に tr_options エントリを追記
        main_yaml_path = "config/main.yaml"
        with open(main_yaml_path, 'r', encoding='utf-8') as f:
            main_data = self.yaml.load(f)

        new_option = self.yaml.map()
        new_option['key'] = key
        new_option['label'] = label
        if requires_environment:
            new_option['requires_environment'] = True

        main_data['menus']['tr_options'].append(new_option)

        with open(main_yaml_path, 'w', encoding='utf-8') as f:
            self.yaml.dump(main_data, f)

        # 2. config/modes/task_report/{key}.yaml を新規作成
        new_yaml_path = f"config/modes/task_report/{key}.yaml"
        new_data = self.yaml.map()
        school_defaults = self.yaml.map()
        pattern_fields = self.yaml.map()

        for field_key, field_val in fields.items():
            if field_val:
                pattern_fields[field_key] = field_val

        school_defaults[key] = pattern_fields
        new_data['school_specific_defaults'] = school_defaults

        with open(new_yaml_path, 'w', encoding='utf-8') as f:
            self.yaml.dump(new_data, f)

        # 3. config をリロード
        print(f"New pattern '{key}' added. Reloading config...")
        config.load_config()
