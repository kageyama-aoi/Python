# 71_SQL_IN句生成

## 概要

ユーザー一覧CSVから **status が Active** のユーザーを抽出し（指定ユーザーは除外）、
SQLの `IN` 句にそのまま貼れるテキストを生成するツール。

```
('alice', 'bob')
```

## 使い方

入力ファイルは次のいずれかで指定する：

- **ドラッグ&ドロップ**: ファイルを `run.bat` にドラッグ&ドロップする
- **ダイアログ選択**: `run.bat` をダブルクリック（00_ランチャーからも起動可）すると
  ファイル選択ダイアログが開く（キャンセルすると安全に中断）
- **コマンドライン**（第2引数で対象列名も指定可）:

```bash
python src/main.py "path/to/users.csv" [列名]
```

### 対応する入力形式

| 形式 | 説明 |
|---|---|
| CSV | 1行目をヘッダーとして読む |
| パイプ区切りテキスト | SQLクライアントの表形式出力（`| a | b |`、`+---+` 罫線は自動スキップ） |
| 行リストテキスト | 1行1値のプレーンテキスト |

### 対象列（IN句にする列）の決まり方

1. コマンドライン第2引数
2. `config/main.yaml` の `filter.user_column`（入力にその列が実在する場合）
3. 列が1つだけのファイルは自動選択
4. 上記で決まらなければ列名選択ダイアログを表示（キャンセルで中断）

### 設定（config/main.yaml）

- `filter.status_value` — 対象とするstatus値（既定: `Active`）。`status` 列がない入力ではフィルタ自体をスキップ
- `filter.exclude_users` — 除外するユーザー名のリスト
- `input.dialog_initial_dir` — ファイル選択ダイアログの初期フォルダ
- `output.include_in_prefix` — `true` で `IN ('a', 'b')` 形式で出力

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
- 抽出結果は重複除去のうえ昇順ソートされる
- 旧 `04_CSV➡in句生成`（旧ミニツール集配下、#91で解散済み）は本ツールに統合済み（#88）。
  旧ツールのタイムスタンプ付き出力は固定ファイル名（`data/output/in_clause.*`）に変更。
  `IN (...)` 形式が必要な場合は `output.include_in_prefix: true` にする
