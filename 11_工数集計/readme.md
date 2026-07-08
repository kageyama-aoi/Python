# 工数集計ツール

タイムシートCSVから工数集計Excelレポートを生成するツール。

## 必要なファイル

| ファイル | 内容 | エンコード |
|---|---|---|
| `input/timesheet.csv` | CrowdLogからダウンロードしたタイムシート | CP932 |
| `input/bugs.csv` | TR/バグ一覧 | UTF-8 |
| `config.json` | 対象プロジェクト・社員の設定 | UTF-8 |

## 設定（config.json）

```json
{
  "target_project": "取引先名",
  "target_employee": "社員名"
}
```

どちらかを空文字にすると全件対象。両方空の場合は起動時に対話的に選択できる。

## 実行方法

```powershell
# PowerShellスクリプトで実行（エラーログが error_log/ に保存される）
input\999_run.ps1

# または直接実行
python main.py
```

## 出力

| ファイル | 内容 |
|---|---|
| `output/工数集計結果_{案件}_{社員}_{日付}.xlsx` | 最終成果物 |
| `output/tr_list.xlsx` | TRリスト |

## テスト

```powershell
python -m pytest tests/
```
