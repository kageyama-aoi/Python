# tframe_api

Tframe関連のAPIリクエスト/レスポンス（JSON）をCSV/TSVに変換するための実験用スクリプト集です。

## ファイル構成

| ファイル | 説明 |
| --- | --- |
| `①request_url_to_json_henkan.py` | リクエストURL（クエリパラメータ付き）をJSON形式に変換する |
| `②reaponse_json_to_tsv.py` | APIレスポンスのJSONをTSVに変換する |
| `csv_to_tsv.py` | CSVファイルをTSVファイルに変換する簡易スクリプト |
| `request_20250930_104636.json` | ①の入出力サンプル |
| `accounts.csv` / `accounts.tsv` | 変換サンプルデータ |
| `sms_fee.csv` / `sms_fee.tsv` | 変換サンプルデータ（SMS料金関連） |

## 使い方

各スクリプトは単体で実行する想定です。ファイル冒頭の入出力パス指定を対象データに合わせて書き換えてから実行してください。

```bash
python ①request_url_to_json_henkan.py
python ②reaponse_json_to_tsv.py
```

## 注意事項

一度きりの調査・変換作業用に作られたスクリプトのため、パスがハードコードされている箇所があります。他のAPI/データで使い回す場合は、対象ファイル名を都度書き換えてください。
