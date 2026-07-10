# 71_SQL_IN句生成

## 概要

ユーザー一覧CSVから **status が Active** のユーザーを抽出し（指定ユーザーは除外）、
SQLの `IN` 句にそのまま貼れるテキストを生成するツール。

```
('alice', 'bob')
```

## 使い方

入力CSVは次のいずれかで指定する（必要な列: `user_name`。`status` 列は任意）：

- **ドラッグ&ドロップ**: CSVファイルを `run.bat` にドラッグ&ドロップする
- **ダイアログ選択**: `run.bat` をダブルクリック（00_ランチャーからも起動可）すると
  ファイル選択ダイアログが開くので、CSVを選ぶ（キャンセルすると安全に中断）
- **コマンドライン**:

```bash
python src/main.py "path/to/users.csv"
```

抽出条件を変えたい場合は `config/main.yaml` を編集する：

- `filter.status_value` — 対象とするstatus値（既定: `Active`）。CSVに `status` 列がない場合はフィルタ自体をスキップ
- `filter.exclude_users` — 除外するユーザー名のリスト
- `input.dialog_initial_dir` — ファイル選択ダイアログの初期フォルダ

## 出力

| ファイル | 用途 |
|---|---|
| `data/output/in_clause.txt` | IN句テキスト。SQLツールに全選択→コピペする用 |
| `data/output/in_clause.csv` | 同じ内容を1セルに入れたCSV。Excelで開く用（BOM付きUTF-8） |

## セットアップ

```bash
pip install -r requirements.txt
```

初回のみ、テンプレートから実設定ファイルを作る（実際の除外ユーザーIDはこちらに書く。
`config/main.yaml` は実データ保護のため git 管理外）：

```bash
copy config\main.example.yaml config\main.yaml
```

## テスト

```bash
python -m pytest tests/ -v
```

## 備考

- 値中のシングルクォートは `''` にエスケープされる
- 抽出結果は昇順ソートされる
- 類似ツール: `33_ミニツール集/04_CSV➡in句生成` は「列を取り出して重複除去→IN句化」する汎用版。
  本ツールは status フィルタ＋除外リスト付きで、条件を YAML で管理する
