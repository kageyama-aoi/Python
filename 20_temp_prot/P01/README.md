# Data Flow Portal (P01)

Excel/CSVで管理している「イベント単位のデータフロー」を、静的HTMLの横表として可視化するツールです。以後のやりとり・文書は日本語で進めます。

## 目的
- CSVの変更履歴をイベント単位で整理し、列ごとの before/after を色分け表示する
- 将来の拡張（検索、列固定、詳細表示、複数CSV）に耐える構成を用意する

## 入出力
- 入力: `data/input/*.csv`（ヘッダ必須）
- 出力: `data/output/portal/index.html` と `assets/style.css`
- 実行ログ: `logs/`

## セットアップ
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 実行
```bash
python scripts/generate_dummy_csv.py
python src/main.py --config config/main.yaml
```

### オプション
- `--input data/input/xxx.csv`（configの入力パスを上書き）
- `--output data/output/portal`（configの出力先を上書き）
- `--open`（生成後にブラウザで開く）

### 入力ファイル指定の実行例
```bash
python src/main.py --config config/main.yaml --input data/input/data_flow_dummy_alt.csv
```

## CSV仕様（概要）
必須列: `case_id`, `attr_type`  
推奨列: `table`, `operation`, `trigger`, `before`, `after`, `note`, `sql`

補完ルール:
- 同一 `case_id` 内では `table/operation/trigger/sql` を省略可能（直前の値を引き継ぐ）
- `case_id` が変わると補完コンテキストはリセット
- `case_id` / `attr_type` 欠落は即エラー（行番号付き）

## 設定（config/main.yaml）
- 入力CSV/出力ディレクトリ
- NULL判定文字列（例: `["NULL","null","None",""]`）
- 固定列名と優先カラム

## 拡張ポイント
- `src/handlers/` に処理を分割済み（読み込み、補完、集約、列計画、HTML生成）
- CSSは `portal_renderer.py` から生成（将来テーマ化しやすい）

## トラブルシュート
- ヘッダ不足: 不足列名が表示されます
- 欠落行: 行番号と行内容の一部が表示されます
- 生成物がない: `logs/` の実行ログを確認してください
