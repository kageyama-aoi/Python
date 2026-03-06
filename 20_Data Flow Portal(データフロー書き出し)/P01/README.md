# Data Flow Portal (P01)

CSV で管理している「イベント単位のデータフロー」を、静的 HTML の横表として可視化するツールです。以後のやりとり・文書は日本語で進めます。

## 目的

- CSV の変更履歴をイベント単位で整理し、列ごとの before/after を色分け表示する
- テーブル単位のグループヘッダ・フィルタ・ツールチップで可読性を確保する
- 将来の拡張（検索・列固定・詳細表示・複数 CSV）に耐える構成を用意する

## 入出力

| 種別 | パス |
|------|------|
| 入力 | `data/input/*.csv`（ヘッダ必須） |
| 出力 HTML | `data/output/portal/index.html` |
| 出力 CSS | `data/output/portal/assets/style.css` |
| ログ | `logs/YYYYMMDD.log` |

## セットアップ

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

依存パッケージ: `pyyaml` のみ

## 実行

```bash
# ダミー CSV を生成してから実行（初回）
python scripts/generate_dummy_csv.py
python src/main.py --config config/main.yaml
```

### CLI オプション

| オプション | 説明 |
|------------|------|
| `--config <path>` | 設定ファイル（デフォルト: `config/main.yaml`） |
| `--input <path>` | 入力 CSV（config の `paths.input_csv` を上書き） |
| `--output <path>` | 出力ディレクトリ（config の `paths.output_dir` を上書き） |
| `--open` | 生成後にブラウザで自動オープン |

### 実行例

```bash
# 別の CSV を指定して生成
python src/main.py --config config/main.yaml --input data/input/data_flow_dummy_alt.csv

# 生成後にブラウザで確認
python src/main.py --config config/main.yaml --open
```

## CSV 仕様

### 必須列

| 列名 | 説明 |
|------|------|
| `case_id` | イベントを識別する ID（変わると補完コンテキストがリセット） |
| `attr_type` | 変更対象の属性名 |

### 推奨列

| 列名 | 補完対象 | 説明 |
|------|----------|------|
| `table` | carry-forward | 対象テーブル名 |
| `operation` | carry-forward | INSERT / UPDATE / DELETE など |
| `trigger` | carry-forward | 変更のトリガー（API名・画面名など） |
| `sql` | carry-forward | 発行された SQL |
| `before` | なし | 変更前の値 |
| `after` | なし | 変更後の値 |
| `note` | なし | 備考 |

### carry-forward ルール

同一 `case_id` 内で `table` / `operation` / `trigger` / `sql` が空欄の場合、直前の行の値を自動補完します。`case_id` が変わると補完コンテキストはリセットされます。

```
case_id, table,    operation, trigger, attr_type,      before, after
CASE-001, orders,  UPDATE,    注文確定, order_status,   NEW,    PAID
CASE-001, ,        ,          ,         order_amount,   1000,   1000   ← table/operation/trigger を補完
```

### イベント集約単位

`(case_id, table)` の組み合わせを 1 行（1 イベント）として集約します。同じ `case_id` でも `table` が異なれば別イベントになります。

### 列キー形式

集約後の列キーは `{table}::{attr_type}`（例: `orders::order_status`）です。HTML テーブルのヘッダはこの `attr_type` 部分を表示します。

## 設定（config/main.yaml）

```yaml
paths:
  input_csv: "data/input/data_flow_dummy.csv"   # デフォルト入力
  output_dir: "data/output/portal"
  assets_dir: "data/output/portal/assets"
  log_dir: "logs"

csv:
  required_columns: [case_id, attr_type]
  carry_forward_columns: [table, operation, trigger, sql]
  null_values: ["NULL", "null", "None", ""]     # NULL とみなす文字列

display:
  fixed_columns: [case_id, trigger, operation, table]  # 左固定列の順序
  priority_columns: []           # 優先表示する列キー（省略時は頻度順）
  show_generated_at: true
  show_input_name: true
  show_legend: true
  table_labels:                  # テーブル物理名 → 論理名のマッピング
    orders: "受注"
    payments: "決済"
  input_candidates:              # 画面上の CSV セレクタに表示するファイル一覧
    - "data/input/data_flow_dummy.csv"
    - "data/input/data_flow_dummy_alt.csv"
```

## HTML 出力の見方

### ヘッダ構成（3 段）

| 段 | 内容 |
|----|------|
| 1段目 | 「対象・フロー（固定）」と「変更カラム」の大区分、凡例 |
| 2段目 | テーブル名グループ（table ごとにまとめてラベル表示） |
| 3段目 | 固定列名 + 各 attr_type 名 |

固定列（`case_id`, `trigger`, `operation`, `table`）は水平スクロール時も左固定されます。

### セル表示パターン

| 状態 | 表示 | 色 |
|------|------|----|
| 新規追加（before=NULL, after=値） | after 値のみ | 緑 |
| 削除（before=値, after=NULL） | before → NULL | 赤 |
| 変更（before != after） | before → after | 黄 |
| 同値（before == after） | before 値 | グレー |
| このイベントでは未変更（現在値あり） | 現在値（イタリック） | ミュート |
| 未変更かつ現在値なし | 空白 | - |

### 行の色分け（operation 別）

| operation | 左ボーダー色 |
|-----------|-------------|
| INSERT | 緑 |
| UPDATE | 黄 |
| DELETE | 赤 |

### ツールチップ

変更セルにカーソルを合わせると `case_id`, `attr_type`, `operation`, `trigger` を含む詳細を表示します。

### フィルタ

ページ上部のドロップダウンで「テーブル絞り込み」「ケース絞り込み」が可能です。列グループも連動して表示・非表示が切り替わります。

## アーキテクチャ

```
src/main.py                         # エントリポイント・引数解析・パイプライン実行
src/config_manager.py               # YAML 読み込み・バリデーション・デフォルトマージ
src/handlers/
    csv_loader.py                   # CSV 読み込み・必須列チェック
    context_filler.py               # carry-forward 補完・欠落行チェック
    event_aggregator.py             # (case_id, table) 単位で集約
    column_planner.py               # 動的列順決定（頻度降順 → 登場順）
    portal_renderer.py              # HTML / CSS 生成・ファイル書き出し
src/utils/
    errors.py                       # UserInputError（行番号・行内容付き）
    fs.py                           # ディレクトリ作成・テキスト書き出し
    log.py                          # 日付別ログファイル + コンソール出力
```

### 処理フロー

```
CSV ファイル
  └─ CsvLoader         → RawRow[] （行番号付き）
       └─ ContextFiller  → FilledRow[] （carry-forward 補完済み）
            └─ EventAggregator → Event[] （(case_id, table) 単位の集約）
            └─ ColumnPlanner   → columns[] （頻度優先の列順）
                 └─ PortalRenderer → index.html + assets/style.css
```

## テスト

```bash
# P01 ディレクトリで実行
python -m unittest tests/test_grouping.py
```

`tests/test_grouping.py`: テーブルグループのヘッダ順序・重複がないことを検証します。

## トラブルシュート

| 現象 | 対処 |
|------|------|
| `CSVヘッダ不足: xxx` | CSV の 1 行目に不足列を追加してください |
| `case_id が欠落しています。line=N` | N 行目の `case_id` を埋めてください |
| `attr_type が欠落しています。line=N` | N 行目の `attr_type` を埋めてください |
| `config not found: xxx` | `--config` のパスを確認してください |
| 出力が空 / エラーなし | `logs/YYYYMMDD.log` で詳細を確認してください |

## 拡張ポイント

- **新しいフィルタ**: `portal_renderer.py` の `build_controls()` に追加
- **テーマ変更**: `build_css()` 内の CSS 変数（`:root`）を編集
- **列の固定追加**: `config/main.yaml` の `display.fixed_columns` を変更
- **複数 CSV のマージ**: `event_aggregator.py` の入力を拡張
- **詳細モーダル**: `render_change()` のツールチップをモーダルに置き換え
