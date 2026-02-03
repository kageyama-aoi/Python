# 設計方針（plan）

## 目的
CSVで管理された「イベント単位の更新履歴」を、静的HTMLの横表として可視化する。将来の検索・フィルタ・詳細モーダル・複数CSVを見据えて、責務分割と設定分離を徹底する。

## データモデル
- RawRow: CSVの1行（行番号付き）
- FilledRow: 省略補完済みの行（case_id内でcarry-forward）
- Event: `case_id` 単位の集約結果
  - meta: table/operation/trigger/sql
  - changes: attr_type -> {before, after, note}

## 処理フロー
1) CsvLoader: CSV読込・ヘッダ検証  
2) ContextFiller: 省略補完（同case_id内のcarry-forward）  
3) EventAggregator: case_id 単位で集約  
4) ColumnPlanner: 動的列抽出（頻度優先→登場順）  
5) PortalRenderer: HTML/CSS生成、出力

## 設定分離（External Config）
- 入力/出力パス、NULL判定、固定列、優先列は `config/main.yaml` に集約。
- コードは「どう動くか」、設定は「何に対して動くか」を分離。

## エラーハンドリング方針
- 必須列不足: 不足列名の一覧を提示。
- case_id/attr_type 欠落: 行番号と行内容の抜粋を提示。
- ユーザーがCSVを修正できる情報に限定して出力。

## 出力仕様（概要）
- イベント=行、attr_type=列の横表。
- before/after を色分け（追加/削除/変更/同値）。
- 行ホバー、operation別の左ボーダー色、凡例を表示。

## 拡張ロードマップ
- フロント: 検索、列フィルタ、固定列数の可変化、詳細モーダル
- バックエンド: 複数CSVのマージ、差分比較
- テスト: HTML生成の存在確認スクリプト追加

## ADR: YAML採用
- 採用理由: 人間が読みやすく、コメントが書けるため。
- 代替案: JSON設定（標準ライブラリのみで実装可能）。
- 方針: PyYAML を requirements に明記し、将来 JSON 化も可能な設計にする。
