# Task Report Automation Tool

Web上のタスクレポートシステムへの入力作業およびCrowdLog（勤怠）の工数実績ダウンロードを自動化するPythonツールです。
**GUIによる直感的な操作**が可能で、設定ファイル（YAML）を編集することで入力内容や対象環境を柔軟に変更できます。

## 特徴

*   **GUI操作**: Tkinterを使用したモダンな選択画面。2段階選択や動的な環境選択により、操作ミスを防ぎます。
*   **Selenium自動化**: ブラウザを自動操作し、ログインからフォーム入力、ダウンロードまでを行います。
*   **拡張性の高いアーキテクチャ**: モードごとにロジック（Handler）と設定（Config）が分離されており、新しいプロジェクトや機能の追加が容易です。

## 前提条件

*   **OS**: Windows (推奨), macOS, Linux
*   **Python**: 3.8 以上
*   **ブラウザ**: Google Chrome (最新版)

## セットアップ手順

1.  **リポジトリのクローン**
    ```bash
    git clone <repository-url>
    cd 01_勤怠自動化
    ```

2.  **仮想環境の作成と有効化**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **依存ライブラリのインストール**
    ```bash
    pip install -r requirements.txt
    ```

4.  **環境変数の設定 (.env)**
    ログイン情報を `.env` ファイルに設定してください。
    ```env
    CROWDLOG_EMAIL=your_email@example.com
    CROWDLOG_PASSWORD=your_password
    ```

## 実行方法

ツールの起動は以下のコマンドで行います。

```bash
python src/main.py
```

コマンドを実行するとGUIウィンドウが立ち上がります。
1.  **モード選択**: 「CrowdLog (勤怠)」または「Task Report (TR)」を選択。
2.  **詳細設定**: TRを選択した場合、プロジェクト種別を選択。「UP依頼」などの場合は対象環境も選択してください。
3.  **実行**: [実行] ボタンを押すとブラウザが起動し、自動処理が開始されます。

## 設定 (Config)

`config/` ディレクトリ配下のYAMLファイルを編集してカスタマイズします。

### ディレクトリ構成
```text
config/
├── main.yaml                # アプリ全体の共通設定 (ダウンロード先など)
└── modes/                   # モードごとの設定
    ├── crowdlog.yaml        # 勤怠関連の設定 (URL, セレクタ)
    └── task_report/         # TR関連の設定
        ├── common.yaml      # TR共通設定 (フィールド定義など)
        ├── shimamura.yaml   # Shimamuraプロジェクト設定
        ├── yamaha.yaml      # Yamahaプロジェクト設定
        └── ...
```

### 設定のカスタマイズ例
新しいTRパターンを追加したい場合は、`config/modes/task_report/` 配下の適切なファイル（例: `shimamura.yaml`）に追記するか、新しいファイルを作成してください。

```yaml
# 例: config/modes/task_report/new_project.yaml
school_specific_defaults:
  np: # 新しいキー
    Project: "NewProjectCode"
    Title: "定型タイトル"
    Comments: "定型コメント"
```
その後、`config/main.yaml` の `menus` セクションに選択肢を追加することで、GUIに表示されるようになります。

## 開発者向け情報 (Architecture)

本ツールは、拡張性を重視して以下の設計を採用しています。

*   **Handlerパターン**: `src/handlers/` 配下にロジックを分割。
    *   `CrowdLogHandler`: 勤怠ダウンロード処理
    *   `TaskReportHandler`: TR入力処理
*   **Config分割**: 設定ファイルもモードごとに分割され、起動時に自動的にマージされます。

### テストの実行
単体テスト（モック使用）により、ロジックの検証が可能です。

```bash
python test_handlers.py
```

## ライセンス

[ライセンス情報を記述]