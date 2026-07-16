# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

巨大CSV/TSVファイルを指定件数ごとに分割するPythonツール。標準ライブラリのみで動作する。
CLI・単体GUI・親フォルダのランチャー（`../launcher_gui.py`）の3経路から実行できる。

## 実行方法

```bash
# CLI（入力ファイルは引数で直接指定。input/ 配置は不要）
python src/run.py <入力CSVファイルパス> [config.json]

# GUI（ファイル選択・解析・実行をウィンドウ上で行う）
python src/gui.py

# テスト
python -m pytest tests
```

## 設定ファイル (config.json)

| キー | 型 | 説明 |
|---|---|---|
| `rows_per_file` | int | 分割単位の行数（1以上の整数） |
| `encoding` | string | `utf-8` / `shift_jis` など |
| `has_header` | bool | `true`: 各分割ファイルにヘッダーを複製、`false`: 全行データとして扱う |
| `delimiter` | string \| null | 区切り文字。`null` または空文字で自動判定（先頭20行の `,` `\t` `;` 出現数 → 拡張子フォールバック） |

GUIは実行時にフォーム内容を config.json へ保存する（次回起動時の初期値になる）。

## アーキテクチャ

- `src/run.py` — コアロジック。`SplitOptions`（実行パラメータ、`from_config_file()`/`validate()`）、
  `SplitResult`（実行結果）、`split_csv()`（分割本体）、`write_log()`、`_detect_delimiter()`。
  CLI エントリポイントを兼ねる。
- `src/analyze.py` — 入力ファイルの事前解析ヘルパー（エンコード判定・行数カウント・先頭行プレビュー・推奨分割行数）。tkinter 非依存。
- `src/gui.py` — 単体GUI（tkinter）。入出力に徹し、処理は `run.py` / `analyze.py` を呼ぶ。
- `config.json` — 実行パラメータ。ツールルートに必置。
- `output/` — 分割済みCSV出力先。ファイル名は `{stem}_split_{001}{ext}` 形式。
- `logs/` — 実行ログ。`split_log_YYYYMMDD_HHMMSS.log` 形式で毎回生成。
- `tests/` — pytest/unittest（`TESTS.md` に仕様一覧）。

## 処理の仕組み

- `csv.reader` / `csv.writer` によるストリーム処理で巨大ファイルをメモリに全展開せず処理する。
- `split_csv(input_path, options, *, output_dir=None, log_dir=None, progress=None)`:
  出力先は引数で差し替え可能（省略時はモジュール定数 `OUTPUT_DIR` / `LOG_DIR`）。
  進捗は `progress` コールバック（10,000行ごと）で通知する — CLI は `print`、GUI はキュー投入を渡す。
- quoting はカンマ区切りのとき `QUOTE_ALL`、それ以外は `QUOTE_MINIMAL`。
- エラー時もログを必ず出力する（`finally` ブロック）。

## 注意

- 親フォルダの `launcher_gui.py` が `python src/run.py <input>` を subprocess で呼ぶため、
  **CLI インターフェース（引数の並び・進捗/完了メッセージの形式）を変える場合はランチャー側も確認する**。
- `input/` `output/` `logs/` は実データが入るため gitignore 対象（実データはコミット禁止）。
