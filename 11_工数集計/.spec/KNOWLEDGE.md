# KNOWLEDGE - ドメイン知識・調査結果

## 業務・ドメイン知識
## 調査・リサーチ結果
## 技術的な知見

## リファクタリング候補一覧

分析日：2026-03-26

### 優先度：高

#### RF-01: `src/main.py` が空ファイル（混乱の元）
- **対象：** `src/main.py`
- **問題：** 1行しかなく実質空。ルートの `main.py` と名前が被り、importミスの原因になりうる。
- **提案：** ファイルを削除するか、ルートの `main.py` の処理をここに移動して役割を明確にする。

#### RF-02: `data_loader.load_timesheet()` が未使用
- **対象：** `src/data_loader.py:10-12`
- **問題：** `load_timesheet()` 関数が定義されているが、実際には `processor.load_and_filter_data()` 内で直接 `pd.read_csv()` が呼ばれており、この関数は使われていない。
- **提案：** 削除するか、`processor.load_and_filter_data()` 内のCSV読み込み部分をこちらに委譲する。

#### RF-03: `add_formulas_and_save()` が肥大化（責務過多）
- **対象：** `src/excel_writer.py:18-99`
- **問題：** 80行超の1関数に「列挿入」「列番号特定」「行ループでの数式埋め込み」「Excel保存」「openpyxl再読み込みと値確定」が混在している。
- **提案：** 以下の3〜4関数に分割する：
  - `_insert_formula_columns(df)` - 列挿入
  - `_embed_formulas(df)` - 数式埋め込みループ
  - `_fix_column_d(wb)` - D列値確定処理

---

### 優先度：中

#### RF-04: `apply_custom_styles()` の列番号・列名がハードコード
- **対象：** `src/excel_writer.py:125-167`
- **問題：** `for i in range(1, 6)` や `column_letter not in ['C','E','O','J']`、`group('F', 'I')` など、列位置が数値・アルファベットのリテラルで直書きされている。列構成が変わると全箇所修正が必要。
- **提案：** `constants.py` にスタイル用の列定義を追加し、そこから参照する。

#### RF-05: `cleanup_old_files()` のパターンが不完全
- **対象：** `main.py:10-18`
- **問題：** `output_summary_*.xlsx` と `Summary_*.xlsx` を削除しているが、現在の出力ファイル名は `Debug_Summary_*.xlsx` と `工数集計結果_*.xlsx` であり、パターンが実態と合っていない。
- **提案：** 実際の出力パターンに合わせてglob式を修正する。

#### RF-06: `temp_file01` のデバッグ用ファイル名が本番コードに残留
- **対象：** `main.py:36`
- **問題：** ファイル名に `Debug_` プレフィックスとランダム5桁数値が含まれており、デバッグ用の痕跡が本番フローに混入している。中間ファイルとして必要なら名前を整理すべき。
- **提案：** `Debug_` を除去し、`temp_` プレフィックスに統一するか、`temp_file02` と同様に短い名前にまとめる。

---

### 優先度：低

#### RF-07: `col_num` の全値チェックが不完全
- **対象：** `src/excel_writer.py:44`
- **問題：** `if not all(col_num.values())` は値が `0`（列インデックス0）の場合も `False` 扱いになりうる（`get_loc` は0始まり）。
- **提案：** `if any(v is None for v in col_num.values())` に変更する。

#### RF-08: `processor.process_details()` のソートキーに `IC.MEMO` が含まれる
- **対象：** `src/processor.py:48-50`
- **問題：** `sort_values` のキーに `IC.MEMO`（メモ文字列）が含まれるが、Noneや空文字が混在すると警告・エラーになる可能性がある。
- **提案：** `na_position='last'` を明示するか、ソートキーから除外を検討する。

---

## 決定事項と理由

### テスト方針
- ソート後のDataFrameに対して `iloc[0]` 等で行順を前提にした検証は脆弱。値の集合（set）で検証する。
- `cleanup_old_files()` のようなファイル操作は `unittest.mock.patch.object(cfg, 'OUTPUT_DIR', tmp_path)` でOUTPUT_DIRをモックして検証できる。
- glob パターンのテストは「削除されるべきファイルが消える」「対象外が残る」の2軸で書くと漏れが少ない。

### RF-03 分割後の設計
- `add_formulas_and_save()` は公開インタフェースとして維持し、内部を4プライベート関数に委譲するパターンにした。
- `_get_col_letters()` の None チェックを `any(v is None for v in col_num.values())` に変更（RF-07対応も兼ねる）。

### RF-05/06 の連動
- globパターン修正（RF-05）と中間ファイル名変更（RF-06）は同じファイル（main.py）の隣接箇所で、同時対応が効率的。
- `random` モジュールのimportも不要になったため合わせて削除。
