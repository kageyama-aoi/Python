# Task Report Automation Tool

Web上のタスクレポートシステムへの入力作業およびCrowdLog（勤怠）の工数実績ダウンロードを自動化するPythonツールです。
**GUIによる直感的な操作**に加え、**実行画面から直接設定を編集・保存**できる機能を備えています。

## 特徴

*   **GUI操作**: Tkinterを使用した選択画面。2段階のモード選択により、目的の操作を迷わず実行できます。
*   **設定エディタ**: [設定編集] ボタンから、プロジェクトごとの定型文（タイトル、コメント等）をGUI上で直接修正・保存できます。
*   **コメント保持保存**: `ruamel.yaml` を採用しており、YAMLファイル内のコメントや空行を維持したまま、GUIからの設定更新が可能です。
*   **拡張性の高いアーキテクチャ**: モードごとにロジック（Handler）と設定（Config）が分離されており、新規プロジェクトの追加が容易です。

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

### 操作フロー
1.  **モード選択**: 「CrowdLog」または「Task Report」を選択。
2.  **設定編集（任意）**: 
    - 選択したプロジェクトの定型文を修正したい場合は、[設定編集] ボタンをクリックします。
    - 編集画面で値を書き換えて [保存] を押すと、実際のYAMLファイルが更新されます。
3.  **実行**: [実行] ボタンを押すとブラウザが起動し、自動処理が開始されます。

## 設定 (Config) の構造

設定は機能ごとに分割されており、`config/modes/` 配下のファイルを直接編集することも可能です。

```text
config/
├── main.yaml                # アプリ全体の共通設定
└── modes/                   # モードごとの設定
    ├── crowdlog.yaml        # 勤怠関連の設定 (URL, セレクタ)
    └── task_report/         # TR関連の設定
        ├── common.yaml      # TR共通設定 (フィールド定義、デフォルト値)
        ├── shimamura.yaml   # Shimamuraプロジェクト設定
        └── ...
```

## 開発者向け情報 (Architecture)

*   **Handlerパターン**: `src/handlers/` 配下のクラスが各モードの具体的な自動化ロジックを担当。
*   **ConfigManager**: `ruamel.yaml` を使用し、コメントを保持したままのYAML読み書きを実現。
*   **単体テスト**: `test_handlers.py` でロジックの検証が可能。

### テストの実行
```bash
python test_handlers.py
```

## ライセンス

[ライセンス情報を記述]
