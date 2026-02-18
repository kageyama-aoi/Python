# Python実行ガイド（入口整理）

## ディレクトリ構成
- `code/`: Pythonスクリプト
- `input/`: 入力CSV/SQL
- `output/`: 生成物

## まずどれを実行するか
1. `code/seikei.py`（最初に実行）
2. SQL整形（手動: `output/03_sql_for_formatter.safe.sql` をフォーマット）
3. `code/restore_formatter_safe_sql.py`
4. `code/split_sql_statements.py`（必要時）
5. `code/extract_join_links.py`（必要時）
6. `code/aggregate_join_links.py`（必要時）

## 最短コマンド
```powershell
python code/seikei.py
python code/restore_formatter_safe_sql.py output/03_sql_for_formatter.safe.sql output/04_sql_restored_from_safe.sql
python code/split_sql_statements.py output/04_sql_restored_from_safe.sql --out-dir output/split_sql --meta-csv output/01_sanitized_with_notes.csv
python code/extract_join_links.py output/split_sql --out output/join_links.csv
python code/aggregate_join_links.py --input output/join_links.csv --output output/join_links_table_pairs.csv --sort table
```

補足:
- `python code/extract_join_links.py output/split_sql` は、`output/split_sql` 配下の最新タイムスタンプフォルダを自動的に対象にします。

## 各ファイルの役割
- `code/seikei.py`: Access風SQLを変換し、CSVとSQL出力を生成（ワークフローの起点）
- `code/restore_formatter_safe_sql.py`: フォーマッタ安全化用トークンを元文字へ復元
- `code/split_sql_statements.py`: SQLを1文1ファイルへ分割し、CSV由来コメントを先頭に付与
- `code/extract_join_links.py`: SQLから結合キー関係を抽出して `output/join_links.csv` を作成
- `code/aggregate_join_links.py`: 抽出結果をテーブルペア単位に集約

## 入出力の基本
- 文字コード前提: 入力は既存運用通り、出力は UTF-8 BOM 系
- 主入力: `input/kennsyuu.csv`
- 主出力: `output/01_sanitized_with_notes.csv`, `output/02_sql_after_conversion.sql`, `output/03_sql_for_formatter.safe.sql`, `output/04_sql_restored_from_safe.sql`
