# このプロジェクトで使われている技術

このドキュメントでは、`open_shortcut` アプリケーションで利用されている主要な技術について、実際のコード例を交えながら解説します。

## 1. GUIフレームワーク: Tkinter

このアプリケーションのグラフィカルユーザーインターフェース（GUI）は、Pythonの標準ライブラリである **Tkinter** を使用して構築されています。`ttk` （Themed Tkinter）ウィジェットを利用することで、OSネイティブのモダンなルックアンドフィールを実現しています。

### 主な役割
- メインウィンドウの作成
- ボタン、ラベル、テキストボックスなどのUIコンポーネントの配置
- ページ（フレーム）の切り替え
- ユーザーのアクション（ボタンクリックなど）のハンドリング

### コード例: ウィジェットの動的生成 (`src/main.py`)

`config.json` の設定に基づいて、ボタンやその他のウィジェットを動的に生成します。以下のコードは、設定エントリの種類に応じて異なるボタン作成メソッドを呼び出すディスパッチャです。

```python
# src/main.py

class DirectoryOpenerApp:
    # ... (抜粋) ...
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
```

## 2. 設定管理: JSON

アプリケーションの挙動は、外部の `data/config.json` ファイルによって完全に定義されます。これにより、コードを直接変更することなく、UIのレイアウト、ボタンのアクション、ウィンドウのタイトルなどを柔軟に変更できます。

### 主な役割
- ウィンドウのタイトルやサイズ
- UIのページ構成
- 各ページに表示されるボタン、セパレータなどの要素
- ボタンが実行するアクション（ディレクトリを開く、URLを開くなど）

### コード例: `data/config.json` の一部

```json
{
  "settings": {
    "window_title": "Open Shortcut",
    "geometry": "400x450",
    "initial_page": "main_menu"
  },
  "pages": {
    "main_menu": {
      "title": "メインメニュー",
      "window_title": "メインメニュー | Open Shortcut",
      "entries": [
        {
          "type": "button",
          "name": "Documents",
          "action": "open_directory",
          "path": "C:\\Users\\kageyama\\Documents"
        },
        {
          "type": "button",
          "name": "各種リンク",
          "action": "open_url",
          "url": "https://docs.google.com/spreadsheets/d/1TfI1uucI9zAlgTnCESs4gsvt_EoAQYQzbY219zMowRA/edit?gid=0#gid=0"
        },
        {
          "type": "separator"
        }
      ]
    }
  }
}
```

## 3. 設定の検証: jsonschema

設定ファイルの形式が正しいことを保証するために、**jsonschema** ライブラリを使用しています。`data/config.schema.json` ファイルに定義されたスキーマ（ルールセット）に基づいて `config.json` を検証し、不正な形式や予期しないキーが含まれている場合はエラーを表示します。

### 主な役割
- 設定ファイルの信頼性向上
- 開発者が意図しない設定ミスによるバグの防止
- エラー発生時の具体的な原因特定

### コード例: 設定の読み込みと検証 (`src/config_manager.py`)

`ConfigManager` クラスが、アプリケーション起動時に設定ファイルを読み込み、検証する責任を負います。

```python
# src/config_manager.py

import jsonschema
from tkinter import messagebox

class ConfigManager:
    # ... (抜粋) ...
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

        except jsonschema.ValidationError as e:
            error_path = " -> ".join(map(str, e.path)) if e.path else "トップレベル"
            error_message = (
                f"設定ファイル '{self.config_path}' の内容に誤りがあります。 ... "
            )
            messagebox.showerror("設定ファイル検証エラー", error_message)
            return None
        # ... (その他の例外処理) ...
```

## 4. 設計思想: 関心の分離 (Separation of Concerns)

このプロジェクトは、コードの保守性と拡張性を高めるために、「関心の分離」という設計原則に基づいています。主なクラスの責務は以下のように分割されています。

- **`DirectoryOpenerApp` (`src/main.py`)**: GUIの表示とユーザーインタラクションのハンドリングに特化。設定データの具体的な読み込みや保存方法は知らない。
- **`ConfigManager` (`src/config_manager.py`)**: 設定ファイルの読み込み、検証、保存、再読み込みといったデータI/Oに関するすべてのロジックを担当。
- **`SettingsEditor` (`src/settings_editor.py`)**: 設定を編集するためのGUIを提供。`ConfigManager` を介して設定を読み書きする。

この設計により、例えば将来的に設定の保存形式をJSONからYAMLに変更したくなった場合でも、変更が必要なのは `ConfigManager` クラスだけであり、GUIのコードに影響を与えることはありません。

## 5. テスト: unittest と unittest.mock

コードの品質を保証し、リファクタリングを安全に行うために、Pythonの標準ライブラリである **unittest** を使用した単体テストが記述されています。

特に **unittest.mock** は、ファイルシステムやウェブブラウザなどの外部依存コンポーネントを「モック（偽物）」に置き換えるために活用されています。これにより、テスト中に実際にディレクトリが開かれたり、ブラウザが起動したりすることなく、ロジックが正しく呼び出されたかだけを検証できます。

### コード例: `ConfigManager` のモック化 (`tests/test_main.py`)

リファクタリング後のテストでは、`DirectoryOpenerApp` が内部で生成する `ConfigManager` をモックに置き換えています。これにより、テストはファイルI/Oから完全に独立し、純粋にGUIのロジックだけを検証できます。

```python
# tests/test_main.py

from unittest.mock import patch, MagicMock

class TestDirectoryOpenerApp(unittest.TestCase):
    # ... (抜粋) ...
    def setUp(self):
        # ...
        # ConfigManagerをDirectoryOpenerAppのインスタンス化の前にパッチする
        with patch('src.main.ConfigManager') as mock_cm_class:
            # セットアップのために実際のconfigを読み込む
            real_cm = ConfigManager(config_path=config_path)
            self.config = real_cm.get_config()

            # 作成されるモックインスタンスを設定
            mock_instance = MagicMock()
            mock_instance.get_config.return_value = self.config
            mock_instance.reload.return_value = True
            
            mock_cm_class.return_value = mock_instance

            # DirectoryOpenerAppが作成されると、このモックを使用する
            self.app = DirectoryOpenerApp(self.root)
            self.mock_config_manager = mock_instance
```