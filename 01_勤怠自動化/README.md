# Task Report Automation Tool

Web上のタスクレポートシステムへの入力作業を自動化するPythonツールです。
設定ファイル (`config.yaml`) を編集することで、入力内容や対象環境を柔軟に変更できます。

## 機能

*   Seleniumを使用したブラウザ自動操作。
*   YAMLファイルによる設定管理（ユーザー、プロジェクト、テンプレート文章など）。
*   コマンドラインからの対話的な実行（学校種別、環境名の選択）。

## 前提条件

*   **OS**: Windows (動作確認済み), macOS, Linux
*   **Python**: 3.8 以上
*   **ブラウザ**: Google Chrome (最新版)
    *   Selenium 4.6以降を使用しているため、ChromeDriverの手動インストールは不要です。

## セットアップ手順

1.  **リポジトリのクローンまたはダウンロード**
    ```bash
    git clone <repository-url>
    cd 00_画面操作自動化
    ```

2.  **仮想環境の作成と有効化 (推奨)**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **依存ライブラリのインストール**
    ```bash
    pip install -r requirements.txt
    ```

## 設定 (config.yaml)

`config.yaml` を編集して、ツールをカスタマイズします。

### 基本設定
*   `app.url`: ターゲットとなるWebアプリケーションのURL。
*   `common_defaults`: 全てのパターンで共通して使用されるデフォルト値（ユーザー名、優先度など）。

### 個別設定 (School Specific Defaults)
`school_specific_defaults` セクションで、学校ごとの入力パターンを定義します。
`common_defaults` との**差分のみ**を記述してください。

例:
```yaml
school_specific_defaults:
  my_new_school:
    Schools: "myschool"
    Project: "NEW_PROJECT_CODE"
    Title: "定型タイトル"
    Comments: "定型コメント"
```

## 実行方法

1.  **ツールの起動**
    ```bash
    python src/main.py
    ```

2.  **対話的な操作**
    画面の指示に従って、操作対象を選択してください。
    *   **Menu 1**: 学校種別や作業種別を選択（YAMLのキーに対応、例: `s`, `y`, `up`）。
    *   **Menu 2**: (`up` 選択時のみ) 対象環境を選択。

3.  **完了**
    ブラウザが自動的に開き、フォームへの入力が行われます。入力が完了するとポップアップでお知らせします。

## ディレクトリ構成

*   `src/`: ソースコードディレクトリ
    *   `main.py`: エントリーポイント
    *   `form_handler.py`: フォーム操作ロジック
    *   `browser_utils.py`: ブラウザ操作ユーティリティ
    *   `config.py`: 設定ファイルローダー
*   `config.yaml`: 設定ファイル
*   `requirements.txt`: 依存ライブラリリスト
*   `logs/`: ログ出力ディレクトリ

## ライセンス

[ライセンス情報をここに記述]
