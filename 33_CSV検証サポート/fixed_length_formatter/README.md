# Fixed Length Formatter — 固定長レコード改行付与

改行が一切ない固定長レコードファイル（1レコード=Nバイト・区切りなし）に、
指定バイト数ごとの改行を付与して読みやすくするPythonツール。標準ライブラリのみで動作する。

## ディレクトリ構成

```text
fixed_length_formatter/
├ src/
│  └ run.py        # コアロジック + CLIエントリポイント
├ tests/           # ユニットテスト
├ config/
│  └ config.json   # 既定値（record_bytes / newline / encoding）。ランチャー実行時に更新される
├ data/            # 実行データ（丸ごとgitignore対象）
│  ├ input/        # 入力置き場（任意。CLIは任意パスを直接指定可能）
│  ├ output/       # 変換結果（実行ごとに <入力名>_<日時>/ サブディレクトリ）
│  └ logs/         # 実行ログ format_log_YYYYMMDD_HHMMSS.log
└ README.md
```

## 使い方

```bash
python src/run.py <入力ファイル> --record-bytes 120 --newline crlf
```

| オプション | 既定 | 説明 |
|---|---|---|
| `--record-bytes N` | config.json の値 | 1レコードのバイト数（固定長仕様書の「レコード長」） |
| `--newline crlf\|lf` | crlf | 出力の改行コード |
| `--encoding ENC` | cp932 | 境界チェック用。変換自体はバイナリで行うため文字は壊れない |

## 仕様・挙動

- **バイト単位**で区切る（CP932の全角=2バイト前提の固定長仕様に対応）
- バイナリストリーム処理（1MB chunk）のため、数GBのファイルでもメモリを消費しない
- 先頭の UTF-8 BOM（EF BB BF）は検出して読み飛ばす（レコード境界がズレないように）
- ファイルサイズが record_bytes で割り切れない場合、末尾の半端レコードも出力し**警告**を記録
- 先頭レコードを `--encoding` でデコードして境界チェック。失敗したら
  「record_bytes が仕様と合っていない可能性」を警告（変換は続行）
- エラー時もログは必ず出力する

## ランチャー連携

親フォルダの `launcher_gui.py` から実行でき、
「変換後、結果を text_splitter の入力にセットする」をONにすると、
変換完了後に text_splitter へ自動で切り替わり変換結果が入力に入る（改行付与→行数分割の流れ作業）。

## テスト

```bash
python -m pytest tests
```
