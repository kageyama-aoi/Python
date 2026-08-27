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

### 初回セットアップ

`data/config.json` は実パスや業務リンクを含むためgit管理外です。
初回は `data/config.example.json` をコピーして `data/config.json` を作成し、内容を自分の環境に合わせて編集してください。

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
│   ├── config.json          # アプリのUIと動作を定義する設定ファイル（git管理外）
│   ├── config.example.json  # 初回コピー元のテンプレート
│   └── config.schema.json   # config.json の構造を定義するスキーマ
├── src/
│   ├── main.py              # エントリポイント。DirectoryOpenerApp（ウィンドウ・リロード統括）
│   ├── ui_builder.py        # 設定に基づくページ／ボタンの動的構築
│   ├── action_handler.py    # ディレクトリ／URL／パラメータ付きURL／ページ遷移の実行
│   ├── config_manager.py    # 設定の読み込み・検証・保存
│   ├── settings_editor.py   # 設定エディタ本体（下記ミックスインを束ねる）
│   ├── settings_tab.py      # 設定エディタ「基本設定」タブ（SettingsTabMixin）
│   ├── pages_tab.py         # 設定エディタ「ページ編集」タブ（PagesTabMixin）
│   ├── button_form.py       # 設定エディタのボタン設定フォーム（ButtonFormMixin）
│   ├── theme.py             # sv_ttk / pywinstyles による任意のダークテーマ適用
│   └── constants.py         # 設定キー・アクション種別などの定数（Enum）
├── tests/
│   ├── test_main.py             # アプリ本体の単体テスト
│   ├── test_settings_editor.py  # 設定エディタのレイアウト回帰テスト
│   └── data/                    # テスト用フィクスチャ
├── docs/                    # 設計メモ・テストガイド・図
├── run.bat / run.ps1       # アプリ起動用ラッパー
├── run_tests.bat / run_tests.ps1  # テスト実行用ラッパー
├── requirements.txt        # 依存ライブラリ
├── README.md               # このファイル
└── docs/TECHNOLOGIES.md    # 使用技術の詳細な解説
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

> **注意（ダークテーマ利用時）**: `sv_ttk`（ダークテーマ）が導入されている環境では、
> ボタンは画像ベースで描画されるため、`styles` や各エントリの `background` は反映されません
> （`foreground`＝文字色は反映されます）。ボタンの色分けは `foreground` と、
> ページ遷移ボタンに自動で乗る `Nav.TButton` スタイルで行ってください。
> `sv_ttk` 未導入時は標準ttkテーマで `background` も反映されます。

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

- [**docs/TECHNOLOGIES.md**](./docs/TECHNOLOGIES.md)

## 依存関係

- Python 3.x
- `jsonschema`（必須）
- `sv-ttk`, `pywinstyles`（任意 / ダークテーマ用。未導入でも標準ttkテーマで動作します）

以下のコマンドで依存ライブラリをインストールできます。
```bash
pip install -r requirements.txt
```
