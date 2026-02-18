# Python実行ガイド（入口整理）

## まずどれを実行するか
1. `seikei.py`（最初に実行）
2. SQL整形（手動: `03_sql_for_formatter.safe.sql` をフォーマット）
3. `restore_formatter_safe_sql.py`
4. `split_sql_statements.py`（必要時）
5. `extract_join_links.py`（必要時）
6. `aggregate_join_links.py`（必要時）

## 最短コマンド
```powershell
python seikei.py
python restore_formatter_safe_sql.py 03_sql_for_formatter.safe.sql 04_sql_restored_from_safe.sql
python split_sql_statements.py 04_sql_restored_from_safe.sql --out-dir split_sql
python extract_join_links.py split_sql
python aggregate_join_links.py --input join_links.csv --output join_links_table_pairs.csv --sort table
```

## 各ファイルの役割
- `seikei.py`: Access風SQLを変換し、CSVとSQL出力を生成（ワークフローの起点）
- `restore_formatter_safe_sql.py`: フォーマッタ安全化用トークンを元文字へ復元
- `split_sql_statements.py`: SQLを1文1ファイルへ分割し、CSV由来コメントを先頭に付与
- `extract_join_links.py`: SQLから結合キー関係を抽出して `join_links.csv` を作成
- `aggregate_join_links.py`: 抽出結果をテーブルペア単位に集約

## 入出力の基本
- 文字コード前提: 入力は既存運用通り、出力は UTF-8 BOM 系
- 主入力: `kennsyuu.csv`
- 主出力: `01_sanitized_with_notes.csv`, `02_sql_after_conversion.sql`, `03_sql_for_formatter.safe.sql`, `04_sql_restored_from_safe.sql`
