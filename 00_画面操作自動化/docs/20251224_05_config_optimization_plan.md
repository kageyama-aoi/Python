# 設定ファイル(YAML)の最適化計画

本ドキュメントは、冗長になっている `config.yaml` の `school_specific_defaults` を最適化し、保守性と拡張性を向上させるための計画書です。

## 1. 目的

*   **重複の排除**: 多くの定義で共通している値（"Critical", "shimamura", "kageyama" など）を何度も記述しなくて済むようにする。
*   **可読性の向上**: リスト形式（`["val1", "val2", ...]`）から辞書形式（`key: value`）に変更することで、どの値が何の設定なのかを一目でわかるようにする。
*   **柔軟性の確保**: 必要な項目だけを記述すれば動くようにする（差分定義）。

## 2. 変更アプローチ

### A. データ構造の変更 (リスト -> 辞書)
現在は順序依存のリスト形式ですが、これをフィールド名をキーとした辞書形式に変更します。

### B. デフォルト値のマージ戦略
1.  YAML内に `common_defaults`（全パターン共通のデフォルト値）を定義します。
2.  各学校タイプ（`s`, `y` など）の設定は、このデフォルト値との**差分のみ**を記述します。
3.  プログラム側で読み込み時に「共通デフォルト」に「個別設定」をマージ（上書き）して、最終的な入力データを生成します。

## 3. YAML構成案 (Before / After)

### Before (現状)
```yaml
school_specific_defaults:
  s: ["shimamura", "SMMs001PH", "Critical", "kageyama", "-", "(UATxxx)-----(shimaXXs)", "kageyama", "sc"]
  y: ["yamaha", "YMHs001PH", "Critical", "kageyama", "-", "(Redminexxx)-----(GXX)", "kageyama", "yc"]
```
*   順序を覚えている必要がある。
*   同じ値が繰り返し登場する。

### After (最適化後)
```yaml
# 共通のデフォルト値
common_defaults:
  Schools: "shimamura"
  Priority: "Critical"
  Uploader: "kageyama"
  Owner: "kageyama"
  Category: "-"
  Project: ""
  Title: ""
  Comments: ""

# 個別の設定（差分のみ記述）
school_specific_defaults:
  s: 
    Project: "SMMs001PH"
    Title: "(UATxxx)-----(shimaXXs)"
    Comments: "sc"
  y:
    Schools: "yamaha"
    Project: "YMHs001PH"
    Title: "(Redminexxx)-----(GXX)"
    Comments: "yc"
```

## 4. コード修正方針

### A. `config.yaml` の修正
上記の After 案に従ってファイルを書き換えます。

### B. `src/form_handler.py` の修正
`fill_form` メソッド内のロジックを変更します。

1.  YAMLから `common_defaults` を取得。
2.  選択されたタイプ（例: `s`）の個別設定を取得。
3.  `common_defaults.copy()` を作成し、そこに個別設定を `.update()` でマージ。
4.  マージされた辞書を使って `input_data` を構築するループ処理を行う。
    *   これまでのようにインデックス（順序）でアクセスするのではなく、フィールド名（キー）で値を取り出す。

## 5. 実施ステップ

1.  **YAML修正**: `config.yaml` を新しい構造に書き換える。
2.  **ロジック修正**: `src/form_handler.py` を辞書マージ方式に対応させる。
3.  **確認**: 以前と同じ挙動になるか確認する。
