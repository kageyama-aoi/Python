# SQL作業フロー（ミス防止版）

## 目的
VS CodeのSQLフォーマットで見やすく整形しつつ、
元の記号（例: `／`, `～` など）は最後に復元できるようにする。

## 実行順（必ずこの順番）

### 1. 変換ファイル作成（Step 1）
以下を実行します。

```powershell
python seikei.py
```

生成されるファイル:
- `01_sanitized_with_notes.csv` : 変換結果 + 注意メモ
- `02_sql_after_conversion.sql` : 変換後SQL（生）
- `03_sql_for_formatter.safe.sql` : フォーマット専用SQL（ここを整形する）

補足:
- 既存の出力ファイルや旧 `kennsyuu_*` ファイルは `archive/` に自動退避されます。

### 2. VS Codeで整形（Step 2-1）
`03_sql_for_formatter.safe.sql` を開いて SQL フォーマットを実行し、保存します。

重要:
- **整形対象は必ず `03_sql_for_formatter.safe.sql`**
- `02_sql_after_conversion.sql` は整形しないでください。

### 3. 記号を復元（Step 2-2）
以下を実行します。

```powershell
python restore_formatter_safe_sql.py 03_sql_for_formatter.safe.sql
```

生成されるファイル:
- `04_sql_restored_from_safe.sql` : 記号復元済みSQL（改行・インデントは維持）

別名で保存した整形ファイルを使う場合:

```powershell
python restore_formatter_safe_sql.py <整形済みsafeファイル> <復元後ファイル>
```

## 注意事項
- `python seikei.py` を再実行すると `01`〜`03` は再生成されます。
- 過去ファイルは `archive/` に残るため、必要ならそこから復元できます。
- 整形結果を活かすには、必ず「整形後の safe ファイル」を `restore_formatter_safe_sql.py` に渡してください。
