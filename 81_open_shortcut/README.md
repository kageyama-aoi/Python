# Open Shortcut

`config.json` ファイルに基づいて、ディレクトリやURLへのショートカットボタンを動的に生成するGUIランチャーアプリケーションです。

## 概要

このアプリケーションは、日常的に使用するフォルダやウェブサイトへのアクセスを効率化することを目的としています。設定ファイルをJSON形式で記述するだけで、GUI上に複数ページのボタンランチャーを自由に構築できます。

また、GUIベースの設定エディタも搭載しており、直感的な操作で設定を管理することが可能です。

## 主な機能

- **動的なUI生成**: `data/config.json` の内容を読み込み、ボタンやページを動的に作成します。
- **多彩なアクション**:
  - ローカルのディレクトリを開く
  - ウェブサイトのURLを開く
  - パラメータ付きのURLを生成して開く (`/users/{userId}` のような形式)
  - アプリケーション内の別ページに切り替える
- **GUIによる設定編集**: アプリケーションに組み込まれた設定エディタで、`config.json` の内容をGUI上で編集・保存できます。
- **設定のリアルタイム検証**: `jsonschema` を利用して設定ファイルの形式を常に検証し、不正な設定によるエラーを未然に防ぎます。
- **カスタマイズ性**: ボタンのアイコン、色、フォントなどを柔軟に設定できます。

## 使い方

### アプリケーションの起動

`run.bat` をダブルクリックすると、アプリケーションが起動します。

```batch
run.bat
```

### テストの実行

開発や変更を行った後、`run_tests.bat` を実行することで、アプリケーションの単体テストを実行できます。

```batch
run_tests.bat
```

## ファイル構成

```
open_shortcut/
├── data/
│   ├── config.json         # アプリケーションのUIと動作を定義する設定ファイル
│   └── config.schema.json  # config.jsonの構造を定義するスキーマファイル
├── src/
│   ├── main.py             # メインのGUIアプリケーション
│   ├── settings_editor.py  # 設定エディタのGUI
│   ├── config_manager.py   # 設定の読み込み・検証・保存を担当するクラス
│   └── constants.py        # 設定キーなどの定数を管理
├── tests/
│   └── test_main.py        # アプリケーションの単体テスト
├── run.bat                 # アプリケーション起動用バッチファイル
├── run_tests.bat           # テスト実行用バッチファイル
├── README.md               # このファイル
└── TECHNOLOGIES.md         # 使用技術の詳細な解説
```

## 設定 (`data/config.json`) の詳細

設定ファイルは主に `settings`, `styles`, `pages` の3つのトップレベルキーで構成されます。

### `settings`

アプリケーション全体のグローバル設定です。

```json
{
  "settings": {
    "window_title": "Open Shortcut",
    "geometry": "400x450",
    "resizable": [false, true],
    "icon_folder": "assets/icons",
    "window_icon": "app_icon.ico",
    "initial_page": "main_menu"
  }
}
```

### `styles`

`ttk`ウィジェットのスタイルを定義します。

```json
{
  "styles": {
    "TButton": { "font": ["Yu Gothic UI", 10], "padding": 5 },
    "Header.TLabel": { "font": ["Yu Gothic UI", 12, "bold"] }
  }
}
```

### `pages`

アプリケーションの各ページと、そこに配置される要素（エントリー）を定義します。

#### エントリーの種類 (`entries`)

##### 1. ディレクトリを開く
```json
{
  "name": "作業フォルダ",
  "action": "open_directory",
  "path": "C:\\path\\to\\your\\folder"
}
```

##### 2. URLを開く
```json
{
  "name": "Google",
  "action": "open_url",
  "url": "https://www.google.com"
}
```

##### 3. ページを切り替える
```json
{
  "name": "別メニューへ",
  "action": "show_page",
  "target": "other_page_name"
}
```

##### 4. パラメータ付きURLを開く
`base_url` 内の `{key}` が、`parameters` で定義されたUIコンポーネントの入力値に置き換えられます。
```json
{
    "name": "GitHub User",
    "action": "open_parameterized_url",
    "base_url": "https://github.com/{username}",
    "parameters": [
        {
            "name": "username",
            "label": "ユーザー名",
            "type": "text",
            "default_value": "your-username"
        }
    ]
}
```

##### 5. 区切り線
```json
{
  "type": "separator"
}
```

## 使用技術

このプロジェクトで使われている技術や設計思想の詳細は、以下のドキュメントを参照してください。

- [**TECHNOLOGIES.md**](./TECHNOLOGIES.md)

## 依存関係

- Python 3.x
- `jsonschema`

以下のコマンドで依存ライブラリをインストールできます。
```bash
pip install jsonschema
```
