# リファクタリング計画書

このドキュメントは、`open_shortcut` プロジェクトの保守性、拡張性、堅牢性を向上させるためのリファクタリング計画を定義します。

## 1. 目的

- **保守性の向上**: コードの可読性を高め、修正やデバッグを容易にする。
- **拡張性の向上**: 新機能の追加を容易にするための柔軟な構造を構築する。
- **堅牢性の向上**: 設定ミスや予期せぬ操作に対する耐性を高める。

---

## 2. ファイル構成の再編案

現在のフラットなファイル構成から、役割ごと（ソースコード、リソースなど）にディレクトリを分割し、より構造化された構成に変更します。

### 現状の構成

```
open_shortcut/
├── icons/
├── 01_open_directory_gui.bat
├── config.json
├── open_directory_gui.py
└── settings_editor.py
```

### 新しい構成案

```
open_shortcut/
├── src/
│   ├── __init__.py
│   ├── main.py                 # (旧 open_directory_gui.py)
│   ├── settings_editor.py
│   ├── config_loader.py        # (新規) 設定読み込み/検証クラス
│   └── action_handler.py       # (新規) アクション実行クラス
├── data/
│   ├── config.json
│   └── config.schema.json      # (新規) バリデーション用スキーマ
├── assets/
│   └── icons/
│       └── ...
├── run.bat                     # (旧 01_open_directory_gui.bat)
└── README.md
```

### 変更のメリット

- **関心の分離**: ソースコード (`src`)、設定ファイル (`data`)、画像などのリソース (`assets`) が明確に分離され、プロジェクトの見通しが良くなります。
- **ポータビリティの向上**: `run.bat` から `src/main.py` を呼び出すように変更することで、実行環境のルートパスを意識せずに済みます。
- **拡張準備**: 新しいモジュール (`config_loader.py`, `action_handler.py`) を追加する準備が整います。

---

## 3. コードのリファクタリング提案

### 提案1: 責務の分割 (Single Responsibility Principle)

- **対象**: `open_directory_gui.py` の `_create_button` メソッド
- **問題点**: 複数のアクション (`open_directory`, `open_parameterized_url` など) のUI構築ロジックが1つのメソッドに混在しており、非常に複雑で読みにくい。
- **解決策**:
  - アクションの種類ごとにUIを構築するヘルパーメソッドを定義します。
    - `_create_simple_action_button()`: `open_directory`, `open_url`, `show_page` 用のシンプルなボタンを作成。
    - `_create_parameterized_url_entry()`: `open_parameterized_url` 用の、パラメータ入力欄を含む複合ウィジェットを作成。
  - `_create_button` メソッドは、`entry` の `action` に応じてこれらのヘルパーメソッドを呼び出すファクトリのように振る舞います。

### 提案2: 定数管理 (Magic Stringの排除)

- **対象**: プロジェクト全体
- **問題点**: `"open_directory"`, `"path"`, `"settings"` のような設定キーの文字列がコード内に直接記述（ハードコード）されています。これにより、タイプミスによるバグや、キー名変更時の修正漏れが発生しやすくなります。
- **解決策**:
  - `src/constants.py` のようなファイルを作成します。
  - `Enum` や定数クラスを用いて、設定ファイルのキーを一元管理します。
    ```python
    # src/constants.py (例)
    from enum import Enum

    class Action(Enum):
        OPEN_DIR = "open_directory"
        OPEN_URL = "open_url"
        SHOW_PAGE = "show_page"
        PARAM_URL = "open_parameterized_url"

    class ConfigKey(Enum):
        SETTINGS = "settings"
        PAGES = "pages"
        ACTION = "action"
        PATH = "path"
        # ...
    ```
  - コード内では `ConfigKey.ACTION.value` のように定数を参照して文字列を取得します。

### 提案3: 設定の動的リロード機能の実装

- **対象**: `main.py` (旧 `open_directory_gui.py`) と `settings_editor.py`
- **問題点**: 設定エディタで設定を保存しても、アプリケーションを再起動しないと変更が反映されません。
- **解決策**:
  1. `SettingsEditor` で保存が成功した際に、メインウィンドウに変更を通知する仕組みを導入します（コールバック関数やカスタムイベント）。
  2. `DirectoryOpenerApp` は通知を受け取ると、UIを再構築するメソッド（例: `reload_ui`）を呼び出します。
  3. `reload_ui` メソッドは、現在のウィジェットをすべて破棄 (`destroy`) し、設定ファイルを再読み込みして、UIを最初から構築し直します。

### 提案4: 設定ファイルのバリデーション

- **対象**: 設定ファイルの読み込み処理
- **問題点**: `config.json` の記述ミス（必須キーの欠落、値の型間違いなど）が、予期せぬ実行時エラーを引き起こす可能性があります。
- **解決策**:
  1. `jsonschema` ライブラリを導入します (`pip install jsonschema`)。
  2. `data/config.schema.json` に、`config.json` が満たすべき構造（プロパティ、型、必須項目など）を定義します。
  3. アプリケーション起動時に設定ファイルを読み込んだ後、`jsonschema.validate()` を使って内容を検証します。
  4. バリデーションに失敗した場合は、どの部分に問題があるかをユーザーに分かりやすく通知し、アプリケーションを安全に終了させます。

### 提案5: クラスの分割

- **対象**: `DirectoryOpenerApp` クラス
- **問題点**: `DirectoryOpenerApp` クラスが、設定の読み込み、UIの構築、イベントハンドリングなど、多くの責務を担っており、肥大化しています。
- **解決策**:
  - **`ConfigLoader`**: 設定ファイル(`config.json`)の読み込み、解析、バリデーションを担当するクラス。
  - **`ActionHandler`**: ボタンクリック時のアクション（ディレクトリを開く、URLを開くなど）の実行ロジックを担当するクラス。
  - **`UIBuilder`**: `ConfigLoader` から受け取った設定情報に基づき、Tkinterウィジェットを構築する責務を持つクラス。
  - `DirectoryOpenerApp` (または `MainApp`) は、これらのクラスを統括し、全体の流れを制御する役割に専念します。

---

## 4. リファクタリングの推奨ステップ

以下の順序で段階的に進めることを推奨します。

1.  **Step 1: ファイル構成の再編**
    - まず、新しいディレクトリ構造を作成し、既存のファイルを移動します。インポートパスやファイルパスの参照を修正します。

2.  **Step 2: 定数管理の導入**
    - `constants.py` を作成し、マジックストリングを定数に置き換えます。影響範囲が広く、早期に着手することで後の作業が楽になります。

3.  **Step 3: 責務の分割 (`_create_button`)**
    - 最も複雑な `_create_button` メソッドを分割し、可読性を改善します。

4.  **Step 4: 設定の動的リロード**
    - アプリケーションの利便性を大きく向上させる機能です。UIの再構築ロジックを実装します。

5.  **Step 5: バリデーションの導入**
    - アプリケーションの堅牢性を高めるために、設定ファイルのスキーマ検証を実装します。

6.  **Step 6: (任意) クラスの分割**
    - プロジェクトがさらに大規模になる場合に備え、クラス分割を検討します。小規模なリファクタリングでは省略可能です。