# Accessクエリ整形ツール

## 構成
- `code/`: 実行スクリプト
- `input/`: 入力ファイル（例: `input/kennsyuu.csv`）
- `output/`: 生成物

## 基本フロー
```powershell
python code/seikei.py
python code/restore_formatter_safe_sql.py output/03_sql_for_formatter.safe.sql output/04_sql_restored_from_safe.sql
python code/split_sql_statements.py output/04_sql_restored_from_safe.sql --out-dir output/split_sql --meta-csv output/01_sanitized_with_notes.csv
python code/extract_join_links.py output/split_sql --out output/join_links.csv
python code/aggregate_join_links.py --input output/join_links.csv --output output/join_links_table_pairs.csv --sort table
```

## 補足
- 既存出力の退避先は `output/archive/`。
- スクリプトはカレントディレクトリに依存せず、プロジェクトルート基準で `input/` と `output/` を参照する。
