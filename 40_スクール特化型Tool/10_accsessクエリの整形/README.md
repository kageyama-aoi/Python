# Accessクエリ整形ツール

## 構成
- `code/`: 実行スクリプト
- `input/`: 入力ファイル（例: `input/kennsyuu.csv`）
- `output/`: 生成物
- `プロンプト運用手引き.md`: 再実行用プロンプト集（v2）
- `コンテキスト定義.md`: プロジェクト前提ルール（推定/確定管理）

## 基本フロー
```powershell
python code/seikei.py
python code/restore_formatter_safe_sql.py output/03_sql_for_formatter.safe.sql output/04_sql_restored_from_safe.sql
python code/split_sql_statements.py output/04_sql_restored_from_safe.sql --out-dir output/split_sql --meta-csv output/01_sanitized_with_notes.csv
python code/extract_join_links.py output/split_sql --out output/join_links.csv
python code/aggregate_join_links.py --input output/join_links.csv --output output/join_links_table_pairs.csv --sort table
```

## このリポジトリでできること
- Access由来SQLの正規化（記号・真偽値・識別子の補正）
- SQL分割とコメント付与
- JOINリンク抽出とテーブルペア集約
- Mermaid ER図の生成（core / full）
- フラグ別ER比較（受講生 / 講師 / 一般研修）
- 差分DIF生成（共通/固有テーブル・リレーション）

## 推奨の参照順
- 解析結果の入口: `output/README_OUTPUT.md`
- 採用版: `output/00_latest/`
- 再依頼時のプロンプト: `プロンプト運用手引き.md`

## 補足
- 既存出力の退避先は `output/archive/`。
- スクリプトはカレントディレクトリに依存せず、プロジェクトルート基準で `input/` と `output/` を参照する。
