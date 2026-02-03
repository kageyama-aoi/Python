# Repository Guidelines

このリポジトリは、CSVのデータフローを静的HTMLへ可視化するツールです。以後のやりとり・文書は日本語で行います。

## プロジェクト構成とモジュール整理

- 実装: `src/`（エントリ: `src/main.py`）
- 設定: `config/main.yaml`（パス、NULL判定、固定列など）
- ドキュメント: `docs/plan.md`
- 入出力: `data/input/` と `data/output/portal/`
- 補助: `scripts/`（例: `generate_dummy_csv.py`）
- ログ: `logs/`

## ビルド・テスト・開発コマンド

- ダミーCSV生成: `python scripts/generate_dummy_csv.py`
- 生成実行: `python src/main.py --config config/main.yaml`
- 任意: `--input` / `--output` / `--open` で上書き可能

## コーディング規約・命名規則

- PythonはPEP 8準拠（4スペース、snake_case）。
- 設定値の直書きは禁止。`config/` を唯一の正とします。
- 処理は `src/handlers/` に責務分割（読み込み・補完・集約・列計画・描画）。

## テスト方針

- フレームワークは未固定。追加する場合は `test_*.py` で統一。
- 最低限、READMEの動作確認チェックリストを満たすこと。

## コミット・プルリクエストの指針

- コミットは短い日本語要約（必要ならコロンで補足）。
- PRには変更概要、関連ドキュメント更新、再現手順を含めてください。

## セキュリティ・設定の注意

- 機密情報は `.env` に保存し、Git管理しません。
- 設定変更時は `docs/plan.md` の方針と整合させてください。
