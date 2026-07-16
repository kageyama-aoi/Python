# CSV / TSV / TXT Splitter

巨大な区切り文字ファイルを指定件数ごとに分割するPythonツール。

## ディレクトリ構成

```text
csv_splitter/
├ src/
│  ├ run.py       # コアロジック + CLIエントリポイント
│  ├ analyze.py   # 入力ファイルの事前解析ヘルパー
│  └ gui.py       # 単体GUI（tkinter）
├ tests/          # ユニットテスト（仕様は tests/TESTS.md）
├ config.json
├ README.md
├ input/          # 入力置き場（任意。CLIは任意パスを直接指定可能）
├ output/
└ logs/
```

## 特徴

- 入力ファイルをCLI引数で直接指定（`input/` フォルダ不要）
- CSV（`,`）/ TSV（`\t`）/ 任意区切り文字ファイルに対応
- 区切り文字は拡張子で自動判定（省略可）、`config.json` で上書きも可能
- ヘッダー有無を `config.json` で切り替え可能
- 出力ファイル名: `input_split_001.csv`, `input_split_002.csv` ...
- `UTF-8` / `Shift_JIS` などのエンコーディングに対応
- 巨大ファイルでも扱えるストリーム処理
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
  "has_header": false,
  "delimiter": "\t"
}
```

| キー | 型 | 省略 | 説明 |
|---|---|---|---|
| `rows_per_file` | int | 必須 | 分割単位の行数 |
| `encoding` | string | 必須 | `utf-8` / `shift_jis` など |
| `has_header` | bool | 省略時 `true` | ヘッダー行の有無 |
| `delimiter` | string | 省略時は拡張子で自動判定 | `.csv`→`,` / その他→`\t` |

- `has_header: true` の場合: 先頭行をヘッダーとして扱い、各分割ファイルにヘッダーを書き込みます。
- `has_header: false` の場合: 全行をデータとして扱います。

2. 実行

```bash
python src/run.py <入力CSVファイルパス>
```

`config.json` のパスを変更する場合は第2引数で指定できます。

```bash
python src/run.py /path/to/input.csv /path/to/config.json
```

### GUI で実行する場合

```bash
python src/gui.py
```

ファイル選択 → 「解析」でエンコード・行数・推奨分割行数を確認 → 「実行」。
フォームの内容は実行時に `config.json` へ保存されます。
親フォルダのランチャー（`../launcher_gui.bat`）からも起動できます。

### テスト

```bash
python -m pytest tests
```

## 出力

- 分割ファイル: `output/`（既存フォルダがあればそのまま使用）
- 実行ログ: `logs/split_log_YYYYMMDD_HHMMSS.log`

## ログに残る情報

- 実行時刻（開始/終了）
- 入力ファイル
- 分割条件（rows_per_file / encoding / delimiter / has_header）
- 総データレコード数
- 出力ファイル数
- 出力ファイルごとのレコード件数
