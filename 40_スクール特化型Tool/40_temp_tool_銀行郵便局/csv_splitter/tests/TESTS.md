# テスト仕様書

実行コマンド：
```bash
python -m unittest discover -s tests
```

標準ライブラリのみ（`unittest` + `tempfile`）。  
`OUTPUT_DIR` / `LOG_DIR` はテスト内で一時ディレクトリに差し替えるため、実際の `output/` / `logs/` を汚染しない。

---

## test_run.py — コアロジック（25件）

### `_detect_delimiter` （5件）

| テスト名 | 内容 |
|---|---|
| `test_comma` | カンマ区切りファイル → `,` を返す |
| `test_tab` | タブ区切りファイル → `\t` を返す |
| `test_semicolon` | セミコロン区切りファイル → `;` を返す |
| `test_fallback_csv_extension` | 区切り文字がないファイルは `.csv` 拡張子 → `,` にフォールバック |
| `test_fallback_tsv_extension` | 区切り文字がないファイルは `.tsv` 拡張子 → `\t` にフォールバック |

### `split_csv` （11件）

**基本分割**

| テスト名 | 内容 |
|---|---|
| `test_exact_split` | 9行を3件ずつ → 3ファイル、各3レコード（端数なし・満杯ケース） |
| `test_split_with_remainder` | 10行を3件ずつ → 4ファイル（3+3+3+1）、最終ファイルは1レコード |
| `test_rows_per_file_larger_than_data` | `rows_per_file` が総行数より大きい → 1ファイルにまとまる |

**ヘッダー制御**

| テスト名 | 内容 |
|---|---|
| `test_header_replicated_in_each_file` | `has_header=True`：各分割ファイルの1行目がヘッダー行と一致する |
| `test_no_header_all_rows_are_data` | `has_header=False`：全行がデータとしてカウントされる |

**TSV対応**

| テスト名 | 内容 |
|---|---|
| `test_tab_delimiter` | タブ区切りファイルが正しく分割される |

**戻り値・ログ**

| テスト名 | 内容 |
|---|---|
| `test_return_types` | 戻り値が `(int, list, Path)` の型である |
| `test_log_file_created_on_success` | 正常実行後にログファイルが生成され `status: SUCCESS` と総行数が記録される |

**エラー系**

| テスト名 | 内容 |
|---|---|
| `test_file_not_found` | 存在しない入力ファイルで `FileNotFoundError` が発生する |
| `test_invalid_rows_per_file_zero` | `rows_per_file=0` で `ValueError` が発生する |
| `test_invalid_rows_per_file_negative` | `rows_per_file=-1` で `ValueError` が発生する |

### `write_log` （6件）

| テスト名 | 内容 |
|---|---|
| `test_success_status` | `status: SUCCESS` がログに書き込まれる |
| `test_error_status` | `status: ERROR` とエラーメッセージがログに書き込まれる |
| `test_data_record_count` | `data_record_count` に正しい件数が記録される |
| `test_created_file_count` | `created_file_count` に正しいファイル数が記録される |
| `test_empty_summaries` | 出力ファイルがない場合 `- (none)` と記録される |
| `test_tab_delimiter_repr` | タブ区切りは `\t` という文字列で記録される（リテラルのタブではなく） |

---

## test_gui_helpers.py — GUIヘルパー関数（19件）

### `_fmt_size` （5件）

| テスト名 | 内容 |
|---|---|
| `test_bytes` | 512 → `512.0 B` |
| `test_kilobytes` | 1,024 → `1.0 KB` |
| `test_megabytes` | 1,048,576 → `1.0 MB` |
| `test_gigabytes` | 1,073,741,824 → `1.0 GB` |
| `test_fractional_kb` | 1,536 → `1.5 KB`（小数点あり） |

### `_suggest_rows` （5件）

| テスト名 | 内容 |
|---|---|
| `test_zero` | 0行 → `不明` を返す |
| `test_large` | 1,000,000行 → 推奨値に `100,000` が含まれる（10分割） |
| `test_medium` | 100,000行 → 推奨値に `10,000` が含まれる |
| `test_small` | 500行 → 最低保証の `1,000` が含まれる |
| `test_contains_約10ファイル` | 結果文字列に `約10ファイル` が含まれる |

### `_detect_encoding_from_file` （3件）

| テスト名 | 内容 |
|---|---|
| `test_utf8_bom` | BOM付きUTF-8ファイル → `utf-8-sig` |
| `test_utf8` | 通常のUTF-8ファイル → `utf-8` |
| `test_shift_jis` | Shift-JISファイル → `shift_jis` または `cp932` |

### `_count_rows` （4件）

| テスト名 | 内容 |
|---|---|
| `test_basic` | 4行のファイル → 4（改行カウント） |
| `test_empty` | 空ファイル → 0 |
| `test_single_row` | 1行のファイル → 1 |
| `test_large_chunk` | 5,000行（1MB超）のファイルでも正確にカウントされる |

### `_read_first_row` （5件）

| テスト名 | 内容 |
|---|---|
| `test_basic` | 3列ファイルの先頭行 → カラム数3、列名がプレビューに含まれる |
| `test_single_column` | 1列ファイル → カラム数1 |
| `test_many_columns_truncated` | 10列ファイル → 先頭8列のみ表示、`+` で省略を示す |
| `test_tab_delimiter` | タブ区切りで正しくカラム数を返す |
| `test_nonexistent_file` | 存在しないファイル → 例外を出さず `(0, '(読み取り失敗)')` を返す |

---

## カバーできていない領域

意図的にテスト対象外としているもの：

- **GUI表示系**（tkinterウィジェット、ボタン操作、ログエリア描画）  
  → 手動確認が現実的
- **エンコードエラーが途中で発生するケース**  
  → ファイル読み込み中の例外パス（ログにERROR記録）
- **巨大ファイルのパフォーマンス**  
  → 機能テストの範囲外
