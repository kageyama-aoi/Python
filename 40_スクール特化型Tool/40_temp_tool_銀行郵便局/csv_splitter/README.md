# CSV Splitter

巨大CSVを指定件数ごとに分割するPythonツール。

## ディレクトリ構成

```text
csv_splitter/
├ run.py
├ config.json
├ README.md
├ output/
└ logs/
```

## 特徴

- 入力ファイルをCLI引数で直接指定（`input/` フォルダ不要）
- ヘッダー有無を `config.json` で切り替え可能
- 出力ファイル名: `input_split_001.csv`, `input_split_002.csv` ...
- `UTF-8` / `Shift_JIS` などのエンコーディングに対応
- 巨大CSVでも扱えるストリーム処理
- 実行条件と結果件数を `logs/` に記録

## 必要環境

- Python 3.8+
- 追加ライブラリ不要

## 使い方

1. `config.json` を編集

```json
{
  "rows_per_file": 50000,
  "encoding": "utf-8",
  "has_header": false
}
```

- `has_header: true` の場合: 先頭行をヘッダーとして扱い、各分割ファイルにヘッダーを書き込みます。
- `has_header: false` の場合: 全行をデータとして扱います。

2. 実行

```bash
python run.py <入力CSVファイルパス>
```

`config.json` のパスを変更する場合は第2引数で指定できます。

```bash
python run.py /path/to/input.csv /path/to/config.json
```

## 出力

- 分割CSV: `output/`（既存フォルダがあればそのまま使用）
- 実行ログ: `logs/split_log_YYYYMMDD_HHMMSS.log`

## ログに残る情報

- 実行時刻（開始/終了）
- 入力ファイル
- 分割条件（rows_per_file / encoding / has_header）
- 総データレコード数
- 出力ファイル数
- 出力ファイルごとのレコード件数
