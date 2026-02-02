# Repository Guidelines

## プロジェクト構成とモジュール構造
- `src/`: アプリ本体。`main.py` が Tkinter のエントリポイントで、UI 構築 (`ui_builder.py`)、アクション処理 (`action_handler.py`)、設定管理 (`config_manager.py`)、設定編集 (`settings_editor.py`) に責務を分離しています。
- `data/`: 実行時設定 (`config.json`) と検証スキーマ (`config.schema.json`)。
- `tests/`: `unittest` ベースのテスト（`test_main.py`）とフィクスチャ（`tests/data/`）。
- `docs/`: 設計メモ、テストガイド、ロードマップ、図。
- ルート: 起動・テスト用スクリプト（`run.bat`, `run.ps1`, `run_tests.bat`, `run_tests.ps1`）。

## ビルド・テスト・開発コマンド
- `python -m src.main` : ソースからアプリを起動。
- `run.bat` / `run.ps1` : Windows 向け起動ラッパー。
- `python -m unittest discover -v tests` : 全テストを詳細表示で実行。
- `run_tests.bat` / `run_tests.ps1` : テスト実行のショートカット。
- `pip install jsonschema` : 必須依存関係をインストール。

## コーディング規約と命名
- Python 3 / 4スペースインデント / UTF-8 を使用。
- 命名規則: 関数・変数・モジュールは `snake_case`、クラスは `PascalCase`、定数・Enum は `UPPER_SNAKE_CASE`。
- 既存設計に合わせ、UI・副作用・設定 I/O を混在させない。
- 既存コードに合わせて型ヒント（例: `dict | None`）を優先。

## テスト方針
- フレームワークは `unittest`。外部副作用（`os.startfile`, `webbrowser`, 設定読込）は `unittest.mock` で隔離。
- テストファイルは `tests/test_*.py`、テストメソッドは `test_*` 命名。
- 新機能追加時は、UI 表示結果の検証とモック呼び出し検証をセットで追加。
- PR 前に `python -m unittest discover -v tests` を必ず実行。

## コミットとプルリクエスト
- 履歴は短い件名（日本語/英語）が中心。命令形で簡潔に記述（例: `設定リロード時の検証を追加`）。
- コミットは関心ごと単位（UI、設定、テスト）で分割。
- PR には目的、主な変更点、テスト結果、UI変更時のスクリーンショット/GIF を含める。
- 関連 Issue をリンクし、`config.json` / スキーマ互換性への影響を明記。

## セキュリティと設定上の注意
- `data/config.json` はユーザー入力として扱い、仕様変更時は `data/config.schema.json` を同時更新。
- 実環境依存の絶対パスは原則コミットしない（必要な場合はテスト用フィクスチャとして明示）。
