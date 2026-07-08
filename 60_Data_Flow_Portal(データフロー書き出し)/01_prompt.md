# Role
あなたは「保守性・拡張性の高い」プロトタイプを作るシニアエンジニアです。
ユーザーがExcel→CSVで管理している“データフロー(イベント単位の更新)”を、静的HTMLとして見やすく表示するツールをPythonで実装してください。
最短ではなく品質重視。将来の拡張（フィルタ、検索、列固定、詳細モーダル、複数CSV等）を見据えた設計と分かりやすいコード構成にしてください。

# MUST: Pythonプロジェクト標準構成定義（厳守）
このプロジェクトは必ず以下の標準構成・設計思想に従うこと。

## 標準ディレクトリ構成（必須）
Project_Root/
├── .gitignore
├── .env                     # ※Git管理外（今回は必須ではないが置ける）
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py              # エントリーポイント
│   ├── config_manager.py    # 設定管理ロジック（YAML読込）
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── fs.py            # ファイル操作/パス補助
│   │   ├── errors.py        # 例外定義・ユーザー向けエラー整形
│   │   └── log.py           # logging設定
│   └── handlers/
│       ├── __init__.py
│       ├── csv_loader.py
│       ├── context_filler.py
│       ├── event_aggregator.py
│       ├── column_planner.py
│       └── portal_renderer.py
├── config/
│   └── main.yaml
├── docs/
│   └── plan.md
├── data/
│   ├── input/
│   │   └── data_flow_dummy.csv
│   └── output/
│       └── portal/
│           ├── index.html
│           └── assets/
│               └── style.css
├── logs/
└── scripts/
    ├── generate_dummy_csv.py
    └── run_build_portal.bat  # 任意（Windows実行補助）

## 設計の3原則（必須）
1) ハードコード禁止（External Config）
   - URL、ファイルパス、列名、NULL表現、固定列名、出力先、スタイル設定などは
     コードに直書きせず config/main.yaml に置く。
2) ロジックと設定の完全分離（Separation of Logic & Config）
   - src/ は「どう動くか」
   - config/ は「何に対して動くか」
3) ドキュメント駆動（Documentation First）
   - 複雑な設計判断、仕様、拡張予定、トレードオフは docs/plan.md にまとめる。

# Non-goals（今回やらない）
- WebサーバやDB連携
- 外部ライブラリ依存（原則標準ライブラリのみ）
  ※ただしYAML読込のために PyYAML を使う場合は requirements.txt に明記し、
    使わない選択肢（JSON設定にする案）も docs/plan.md に比較として記載する。
- 編集UI（閲覧のみ）

# Deliverables（成果物）
以下のファイル一式を生成してください。

1) README.md
   - 目的、入出力、セットアップ、実行方法、CSV仕様、設定方法、拡張ポイント、トラブルシュート
2) config/main.yaml
   - 入力CSV、出力先、NULL扱い、固定列名、色分けルール、列順ルールなど
3) docs/plan.md
   - 設計方針、データモデル、処理フロー、拡張ロードマップ、意思決定ログ（ADR風でも可）
4) scripts/generate_dummy_csv.py
   - 実行すると data/input/data_flow_dummy.csv を生成する
5) data/input/data_flow_dummy.csv
   - ダミーデータ（仕様を満たす）
6) src/main.py
   - CLIエントリ（--config 指定、入力上書き指定など）
7) src/config_manager.py
   - YAML（or JSON）読み込み、バリデーション、デフォルト適用
8) src/handlers/*.py
   - 読み込み→補完→集約→列計画→HTML生成
9) src/utils/*.py
   - 例外、ログ、パス操作
10) data/output/portal/index.html と assets/style.css（生成物）
   - main.py 実行で生成される

# CLI仕様（必須）
- 基本実行：
  python src/main.py --config config/main.yaml
- オプション（推奨）：
  --input data/input/xxx.csv（configより優先）
  --output data/output/portal（configより優先）
  --open（可能なら生成後にブラウザで開く。難しければREADMEに手動手順）
- 実行ログは logs/ に出力（logging）

# CSV仕様（入力）
ファイル：任意（例：data/input/data_flow.csv）
ヘッダ必須（列順は固定推奨）

- event_id          : 必須。イベントのグルーピングキー（例：E001）
- table             : 省略可。同一event_id内で最初に書けばよい。以降は空でOK
- operation         : 省略可。例：INSERT/UPDATE/DELETE
- trigger           : 省略可。例：画面名/API/バッチ名など
- attr_type         : 必須。変更対象のカラム名（例：status, paid_at）
- before            : 省略可。値（NULLや空もあり）
- after             : 省略可。値（NULLや空もあり）
- note              : 省略可。補足
- sql               : 省略可。代表SQL（同一event_id内の先頭にだけ書く想定）

## 省略（補完）ルール（必須）
- 同一 event_id 内で table/operation/trigger/sql が重複する場合、2行目以降は空欄でOK
- 空欄は「未指定」であり、同一 event_id の直前の値を引き継ぐ（補完する）
- event_id が変わったら補完コンテキストをリセット
- event_id が欠落している行は即エラー（行番号付き）
- attr_type が欠落している行も即エラー（行番号付き）
- 補完できない必須列（event_id/attr_type以外でも設定で必須化した場合）はエラー

# 表示仕様（出力HTML）
## 表示モード
- 横表（イベント=行、カラム=列）

## 固定列（左側）
- event_id, table, operation, trigger
- 固定列名は config/main.yaml で変更可能

## 動的列（右側）
- CSV全体から attr_type を重複除去して列枠を生成
- セル内容は "before → after" を基本とする
- 当該イベントで変更がない列は空白

## 列順ルール（必須）
- 変化頻度（attr_typeの出現回数）が高いほど左
- 同率の場合は登場順（CSV上で最初に現れた順）で左
- さらに上書きルール（任意）：
  - configで「優先カラム（常に最左寄せ）」を指定できるようにしても良い

## before/after 色分け（必須）
- before==after（同値）: グレー表示（矢印省略可）
- beforeがNULL/空 → afterに値 : afterは緑（added）
- beforeに値 → afterがNULL/空 : afterは赤（removed）
- 値→値の変更 : beforeグレー、after太字（changed）、矢印あり
- NULL表記は "NULL" も空文字も両方許容し、判定できること
- 判定対象のNULL文字列は config で変更可能（例：["NULL", "null", "None", ""]）

## 視認性（必須）
- 横スクロール許容（tableが広がるため）
- 行ホバーで薄くハイライト
- operationに応じた左ボーダー色（UPDATE/INSERT/DELETE）
- 上部に凡例（色の意味）
- 生成日時、入力CSV名を表示

# 実装要件（品質・拡張性・補修性）
## アーキテクチャ（必須）
- 標準ライブラリ中心
- 役割ごとに関数/クラスを分割し、責務を明確にする
  - CsvLoader：CSV読込・ヘッダ検証
  - ContextFiller：省略補完（同event_id内のcarry-forward）
  - EventAggregator：event_idでイベント化（変更点を束ねる）
  - ColumnPlanner：動的列抽出、頻度/登場順で並び替え
  - PortalRenderer：HTML生成（テンプレをコード内に保持してOK）
  - CssWriter：CSS生成（外部ファイルに出力）
- src/utils に以下を用意
  - errors.py：例外クラス（UserInputError等）とメッセージ整形
  - log.py：logging設定（ファイル出力＋コンソール）
  - fs.py：ディレクトリ作成、パス解決、ファイル書込

## エラーハンドリング（必須）
- CSVヘッダ不足は「不足列名一覧」を表示
- event_id/attr_type欠落は「行番号」「該当行の断片」も出す
- 例外メッセージはユーザーがCSVを直せる内容にする

## テスト（推奨だが必須ではない）
- 最低限、READMEに「動作確認チェックリスト」を用意
- 余力があれば scripts/verify_output.py を追加しHTML生成の存在確認をする

# ダミーデータ（必須条件）
scripts/generate_dummy_csv.py が生成する data/input/data_flow_dummy.csv には以下を含めること：
- event_idが複数（E001〜E006程度）
- 同一event_idでtable/operation/trigger/sqlを省略している行がある
- status, paid_at, canceled_at, amount, deleted_flag など複数カラム
- before==after の行が混じる
- NULL→値、値→NULL、値→値変更の3種が混じる
- 変更がないカラムはイベント行のセルが空になることを確認できる
- operationはINSERT/UPDATE/DELETEが最低1回ずつ登場（任意だが推奨）

# 実行手順（READMEに必ず記載）
1) python scripts/generate_dummy_csv.py
2) python src/main.py --config config/main.yaml
   （必要なら --input / --output で上書き）
3) data/output/portal/index.html をブラウザで開く
4) logs/ に実行ログが出ていることを確認

# Output format（あなたの回答の出し方）
- まずディレクトリ構成を提示
- 次に README.md（全文）
- 次に config/main.yaml（全文）
- 次に docs/plan.md（全文）
- 次に scripts/generate_dummy_csv.py（全文）
- 次に src/main.py, src/config_manager.py（全文）
- 次に src/handlers/*.py と src/utils/*.py（全文）
- 最後に「受け入れ基準（動作確認チェックリスト）」を箇条書きで提示

# Acceptance Criteria（受け入れ基準）
- generate_dummy_csv.py 実行で data/input/data_flow_dummy.csv が生成される
- main.py 実行で data/output/portal/index.html と assets/style.css が生成される
- index.html はイベント=行、カラム=列の横表になっている
- attr_typeから動的列が生成され、空欄セルが許容される
- before/after色分けルールが適用される
- 列順が変化頻度優先→登場順で決まる
- 同一event_id内の省略情報が補完される
- event_id/attr_type欠落時のエラーが分かりやすい（行番号付き）
- ログが logs/ に出力される
