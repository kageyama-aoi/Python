# Open Shortcut

`config.json` ファイルに基づいて、ディレクトリやURLへのショートカットボタンを動的に生成するGUIランチャーアプリケーションです。

!App Screenshot

## 概要

このアプリケーションは、日常的に使用するフォルダやウェブサイトへのアクセスを効率化することを目的としています。設定ファイルを編集するだけで、GUI上にボタンを自由に追加・変更できます。また、GUIベースの設定エディタも搭載しており、直感的な操作で設定を管理できます。

## 主な機能

- **動的なGUI生成**: `config.json` の内容を読み込み、ボタンやページを動的に作成します。
- **多彩なアクション**:
  - ローカルのディレクトリを開く
  - ウェブサイトのURLを開く
  - パラメータ付きのURLを生成して開く
  - アプリケーション内の別ページに切り替える
- **GUIによる設定編集**: アプリケーションに組み込まれた設定エディタで、`config.json` の内容をGUI上で編集できます。
- **カスタマイズ性**: ボタンのアイコン、色、フォントなどを柔軟に設定できます。

## ファイル構成

```
open_shortcut/
├── icons/
│   ├── app_icon.ico
│   └── ... (button icons)
├── 01_open_directory_gui.bat
├── config.json
├── open_directory_gui.py
└── settings_editor.py
```

- **`open_directory_gui.py`**: メインのGUIアプリケーション。
- **`settings_editor.py`**: `config.json`を編集するための設定エディタGUI。
- **`config.json`**: アプリケーションの動作、表示内容、スタイルなどを定義する設定ファイル。
- **`01_open_directory_gui.bat`**: アプリケーションを起動するためのバッチファイル。
- **`icons/`**: ボタンやウィンドウに使用するアイコン画像を格納するフォルダ。

## 使い方

1.  `config.json` を直接編集するか、アプリケーションの「設定」ボタンから設定エディタを起動して、開きたいディレクトリやURLを登録します。
2.  `01_open_directory_gui.bat` をダブルクリックしてアプリケーションを起動します。

## 設定 (`config.json`) の詳細

設定ファイルは主に `settings`, `styles`, `pages` の3つのセクションで構成されます。

### `settings`

アプリケーション全体のグローバル設定です。

```json
{
  "settings": {
    "window_title": "ディレクトリを開く",
    "geometry": "400x500",
    "resizable": [true, true],
    "icon_folder": "icons",
    "window_icon": "app_icon.ico",
    "default_button_icon": "default_icon.png",
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

アプリケーションの各ページと、そこに配置されるボタン（エントリー）を定義します。

```json
{
  "pages": {
    "main_menu": {
      "title": "メインメニュー",
      "entries": [
        // 各種エントリー
      ]
    }
  }
}
```

#### エントリーの種類 (`entries`)

##### 1. ディレクトリを開く

```json
{
  "name": "作業フォルダ",
  "action": "open_directory",
  "path": "G:\\マイドライブ\\作業フォルダ"
}
```

##### 2. URLを開く

```json
{
  "name": "各種リンク",
  "action": "open_url",
  "url": "https://docs.google.com/spreadsheets/..."
}
```

##### 3. ページを切り替える

```json
{
  "name": "テストメニューへ",
  "action": "show_page",
  "target": "test_tframe"
}
```

##### 4. パラメータ付きURLを開く

`base_url` 内の `{key}` が、`parameters` で定義されたUIコンポーネントの入力値に置き換えられます。

```json
{
    "name": "testサイト",
    "action": "open_parameterized_url",
    "base_url": "https://tcns.shimamura.co.jp/{kannkyou}",
    "parameters": [
        {
            "name": "kannkyou",
            "label": "環境",
            "type": "pulldown",
            "options": ["testgcp", "dev", "staging"],
            "default_value": "testgcp"
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

## 依存関係

- Python 3.x
- (標準ライブラリのみで動作します)