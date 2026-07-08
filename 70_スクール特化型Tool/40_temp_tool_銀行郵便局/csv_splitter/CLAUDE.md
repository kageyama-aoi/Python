# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

巨大CSVファイルを指定件数ごとに分割するPythonツール。標準ライブラリのみで動作する。

## 実行方法

```bash
python split_csv.py
```

設定は `config.json` で行い、入力ファイルは `input/` に配置する。

## 設定ファイル (config.json)

| キー | 型 | 説明 |
|---|---|---|
| `input_file` | string | `input/` フォルダ内のCSVファイル名 |
| `rows_per_file` | int | 分割単位の行数（1以上の整数） |
| `encoding` | string | `utf-8` / `shift_jis` など |
| `has_header` | bool | `true`: 各分割ファイルにヘッダーを複製、`false`: 全行データとして扱う |

## アーキテクチャ

- `split_csv.py` — エントリポイント兼ロジック本体。`split_csv()` 関数と `write_log()` 関数のみ。
- `config.json` — 実行パラメータ。スクリプトと同じディレクトリに必置。
- `input/` — 入力CSV置き場。
- `output/` — 分割済みCSV出力先。ファイル名は `{stem}_split_{001}.csv` 形式。
- `logs/` — 実行ログ。`split_log_YYYYMMDD_HHMMSS.log` 形式で毎回生成。

## 処理の仕組み

- `csv.reader` / `csv.writer` によるストリーム処理で巨大ファイルをメモリに全展開せず処理する。
- 出力は常に `csv.QUOTE_ALL` で書き込む。
- エラー時もログを必ず出力する（`finally` ブロック）。
