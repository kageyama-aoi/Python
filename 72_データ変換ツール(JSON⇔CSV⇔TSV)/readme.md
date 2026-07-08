# 72_データ変換ツール（JSON⇔CSV⇔TSV）

JSON・CSV・TSV間の変換を行う小さなスクリプト集です。もともと別々のフォルダ（`JSON⇒TSV`・`tframe_api`）に分かれていた、役割の重なるスクリプトを1つにまとめたものです。

## スクリプト一覧

| スクリプト | 変換 | 説明 |
| --- | --- | --- |
| `json_to_tsv_columns.py` | JSON → TSV | カレントフォルダ内の最新JSONを自動検出。階層パスを**横方向のLevel列**に展開し、同じ値が連続する場合は`→`で省略表示。出力は`output_{タイムスタンプ}.tsv`、古い出力は自動で`old/`へ退避 |
| `json_to_tsv_rows.py` | JSON → TSV | カレントフォルダ内の最新JSONを自動検出。階層を**縦方向のLevel/Key/Value行**に展開。ネストの深さが不揃いなデータや、行単位で見比べたい場合向け。出力は`output_levels.tsv`（上書き） |
| `csv_to_tsv.py` | CSV → TSV | カレントフォルダ内の全CSVファイルを一括でTSVに変換 |
| `request_to_json.py` | クエリ文字列 → JSON | `loginId=xxx&pwd=yyy`のようなURLクエリ文字列を対話入力し、JSON形式に変換・保存 |

## 使い分け

同じJSONでも、見たい形式に応じて2種類のJSON→TSV変換を選べます。

- **`json_to_tsv_columns.py`**: 配列を含む複雑な階層データを、パスの共通部分を省略しながら俯瞰したい場合
- **`json_to_tsv_rows.py`**: ネストが浅いデータを、キーと値の対応がひと目で分かる行形式で見たい場合

## 使い方

変換したいファイルをこのフォルダに置いて実行するだけです。

```bash
python json_to_tsv_columns.py   # または json_to_tsv_rows.py
python csv_to_tsv.py
python request_to_json.py
```

## 経緯

- `json_to_tsv_columns.py`は旧`JSON⇒TSV/pg1.py`、`json_to_tsv_rows.py`は旧`tframe_api/②reaponse_json_to_tsv.py`を統合したものです（後者は元々JSONがハードコードされていたため、前者と同様にファイル自動検出方式に修正しています）。
- 各フォルダに残っていた作業データ（会員大会JSON、Tframe APIのサンプルCSV/TSV等）は`_archive/72_73_旧データ/`に退避しています。
