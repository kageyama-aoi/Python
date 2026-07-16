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
├ config.json     # 最後に使った設定
├ presets.json    # 名前付きプリセット（gitignore対象。形式は presets.example.json 参照）
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
- 出力は実行ごとのサブディレクトリ `output/入力名_日時/` に分かれる（再実行しても上書きされない）
- 出力ファイル名: `input_split_001.csv`, `input_split_002.csv` ...
- よく使う設定を名前付きプリセットとして保存・呼び出し可能（GUI / CLI `--preset`）
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

### 名前付きプリセット（お気に入り設定）

よく使う設定の組み合わせは `presets.json` に名前付きで保存できます。

```bash
python src/run.py /path/to/input.csv --preset "大容量分割（45,000行・ヘッダーなし）"
```

- 初回は `presets.example.json` をコピーして `presets.json` を作成（または GUI の「保存...」で作成）
- GUI では「お気に入り」コンボボックスで選択 → フォームに即反映。「保存...」で現在のフォーム内容を名前を付けて登録、「削除」で削除
- `presets.json` は gitignore 対象（実案件名を入れても公開リポジトリに載らない）

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

- 分割ファイル: `output/<入力名>_<YYYYMMDD_HHMMSS>/`（実行ごとにサブディレクトリを作成）
- 実行ログ: `logs/split_log_YYYYMMDD_HHMMSS.log`（出力先サブディレクトリも記録）

## ログに残る情報

- 実行時刻（開始/終了）
- 入力ファイル
- 分割条件（rows_per_file / encoding / delimiter / has_header）
- 総データレコード数
- 出力ファイル数
- 出力ファイルごとのレコード件数
