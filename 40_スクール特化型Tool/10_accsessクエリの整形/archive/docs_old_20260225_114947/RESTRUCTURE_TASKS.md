# ディレクトリ再編タスク一覧

## 目的
- リポジトリを次の方針で整理する。
1. Pythonコードを `code/` に集約する。
2. 入力SQL/CSVを `input/` に集約する。
3. 出力成果物を `output/` に集約する。
4. 階層変更後も各スクリプトが動作するようにする。
5. ドキュメントを新構成に合わせて更新する。

## フェーズ1: 現状調査
- [x] `.py` ファイルを列挙し、エントリポイント/補助スクリプトを分類する。
- [x] 各スクリプト内の相対パス固定参照を洗い出す。
- [x] 旧パスや旧実行コマンドを記載しているドキュメントを特定する。
- [x] 移設前に各スクリプトの期待動作を確認する。

## フェーズ2: 目標構成の定義
- [x] 目標ディレクトリ構成を確定する。
  - `code/`（Python）
  - `input/`（入力ファイル）
  - `output/`（出力ファイル）
  - `output/archive/`（退避ファイル）
- [x] 互換用ラッパー（ルートの実行用 `.py`）を残すか決める。
- [x] `pathlib.Path` でプロジェクトルート基準に統一する方針を決める。

## フェーズ3: ディレクトリ作成とファイル移設
- [x] `code/`, `input/`, `output/`, `output/archive/` を作成する。
- [x] 次のPythonファイルを `code/` へ移動する。
  - `seikei.py`
  - `restore_formatter_safe_sql.py`
  - `split_sql_statements.py`
  - `extract_join_links.py`
  - `aggregate_join_links.py`
- [x] 入力用ファイルを `input/` へ移動する。
- [x] 生成物を `output/` へ移動する。

## フェーズ4: 階層変更に伴うコード修正
- [x] `seikei.py` の既定パスを更新する。
  - 入力既定値: `input/...`
  - 出力既定値: `output/...`
  - アーカイブ既定値: `output/archive`
- [x] `restore_formatter_safe_sql.py` の既定出力先を新構成へ更新する。
- [x] `split_sql_statements.py` の既定値を更新する。
  - メタCSV既定: `output/...`（または決定した正本パス）
  - 分割出力既定: `output/split_sql`
- [x] `extract_join_links.py` の既定出力先を `output/join_links.csv` に更新する。
- [x] `aggregate_join_links.py` の既定入出力先を `output/...` に更新する。
- [x] カレントディレクトリに依存せず実行できるようパス解決を統一する。

## フェーズ5: 仮実行と動作確認
- [x] `python code/seikei.py --help` を実行する。
- [x] `python code/restore_formatter_safe_sql.py --help` を実行する。
- [x] `python code/split_sql_statements.py --help` を実行する。
- [x] `python code/extract_join_links.py --help` を実行する。
- [x] `python code/aggregate_join_links.py --help` を実行する。
- [x] サンプル入力で一連の仮実行を行い、`output/` 配下に出力されることを確認する。

## フェーズ6: ドキュメント更新
- [x] `PYTHON_EXECUTION_GUIDE.md` を新パス・新コマンドに更新する。
- [x] `WORKFLOW.md` を新ディレクトリ前提に更新する。
- [x] 必要に応じて `README.md` を追加/更新する。
  - ディレクトリ構成
  - クイックスタート
  - `input/` / `output/` / `code/` の運用ルール
- [x] 全ドキュメントでコマンド表記を統一する。

## フェーズ7: 最終確認
- [x] 再編後の `.gitignore` 挙動を確認する。
- [x] 旧ルート前提のパス参照がコード内に残っていないことを確認する。
- [x] 移設時に既存データを誤削除していないことを確認する。
- [x] 最終 `git diff` を確認し、意図した変更のみであることを確認する。

## 実装前に決めること
- [x] 互換用ラッパーを残すか（`python seikei.py` を維持するか）。
- [x] `input/` に置く正本入力ファイルはどれか。
- [x] 既存 `archive/` と `split_sql/` の過去データを今回移設するか、現状維持にするか。
