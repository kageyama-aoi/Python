# Task Report Automation Tool

Web上のタスクレポートシステムへの入力作業およびCrowdLog（勤怠）の工数実績ダウンロードを自動化するPythonツールです。
**GUIによる直感的な操作**に加え、**実行画面から直接設定を編集・保存**できる機能を備えています。

## 特徴

*   **GUI操作**: Tkinterを使用した選択画面。2段階のモード選択により、目的の操作を迷わず実行できます。
*   **設定エディタ**: [設定編集] ボタンから、プロジェクトごとの定型文（タイトル、コメント等）をGUI上で直接修正・保存できます。
*   **パターン追加**: [＋ パターン追加] ボタンから、新しいTRパターンをGUIのみで追加できます。YAMLの手動編集は不要です。
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
    cd 02_スクレイピング（勤怠・TR)
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
2.  **TRパターン選択**: Task Report選択時は、対象プロジェクトのパターンをラジオボタンで選択。
3.  **設定編集（任意）**: [設定編集] ボタンから定型文（タイトル・コメント等）をGUI上で修正・保存。
4.  **パターン追加（任意）**: [＋ パターン追加] ボタンから新規パターンを追加。追加後はGUIに即反映されます。
5.  **実行**: [実行] ボタンを押すとブラウザが起動し、自動処理が開始されます。

## 設定 (Config) の構造

設定は機能ごとに分割されており、`config/modes/` 配下のファイルを直接編集することも可能です。

```text
config/
├── main.yaml                # アプリ全体の共通設定・メニュー定義・Schoolsマスターデータ
└── modes/                   # モードごとの設定
    ├── crowdlog.yaml        # 勤怠関連の設定 (URL, セレクタ)
    └── task_report/         # TR関連の設定
        ├── common.yaml      # TR共通設定 (フィールド定義、デフォルト値)
        ├── shimamura.yaml   # Shimamuraプロジェクト設定
        ├── yamaha.yaml      # Yamahaプロジェクト設定
        ├── tframe.yaml      # Tframeプロジェクト設定
        └── {key}.yaml       # [＋ パターン追加] で自動生成されるファイル
```

## 開発者向け情報 (Architecture)

### ディレクトリ構成

```text
src/
├── main.py              # エントリーポイント
├── config/              # 設定管理
│   ├── config.py        # YAML読み込み・グローバルCONF管理
│   └── config_manager.py # GUI経由でのYAML読み書き (ruamel.yaml)
├── gui/                 # UI層
│   ├── gui.py                    # メイン選択画面
│   ├── gui_config_dialog.py      # 設定編集ダイアログ
│   └── gui_add_pattern_dialog.py # パターン追加ダイアログ
├── scraping/            # 自動化ロジック
│   ├── browser_utils.py          # Chrome操作ユーティリティ
│   ├── handler_factory.py        # Handlerの生成
│   └── handlers/
│       ├── base_handler.py           # Handlerの基底クラス
│       ├── crowdlog_handler.py       # 勤怠ダウンロード処理
│       ├── task_report_handler.py    # TR入力処理
│       └── shimamura_search_handler.py # Shimamuraマージ依頼処理
└── utils/               # 汎用ユーティリティ
    └── file_utils.py
```

*   **Handlerパターン**: `src/scraping/handlers/` 配下のクラスが各モードの具体的な自動化ロジックを担当。
*   **ConfigManager**: `ruamel.yaml` を使用し、コメントを保持したままのYAML読み書きを実現。`add_pattern()` メソッドでパターンの新規追加にも対応。

### テストの実行

ブラウザ不要のユニットテストを `tests/` に整備しています。

```bash
# 通常実行（コンソール表示のみ）
python -m pytest tests/ -v

# 結果をファイル保存（.output/test_YYYYMMDD_HHMMSS.txt に保存）
python tests/run_tests.py
```

| テストファイル | 対象 | テスト数 |
|---|---|---|
| `tests/test_config.py` | `config.py`（YAML読み込み・マージ・テンプレート） | 18件 |
| `tests/test_config_manager.py` | `config_manager.py`（パターン追加・設定保存） | 18件 |

## ライセンス

[ライセンス情報を記述]
