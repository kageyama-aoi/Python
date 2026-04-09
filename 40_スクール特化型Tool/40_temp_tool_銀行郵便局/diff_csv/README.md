# 郵便番号 CSV 差分チェックツール

2つの郵便番号CSVファイルを比較し、追加・廃止・共通の郵便番号を特定するツール群。

---

## できること

| スクリプト | 概要 |
|---|---|
| `compare_postcode.py` | 旧・新2ファイルの郵便番号を集合演算で比較し、差分を3つのCSVに出力する |
| `enrich_postcode_issue_info.py` | 新ファイルの各行に「旧ファイルに既存か・今回新規か」の推定情報列を付与して出力する |

---

## 想定シチュエーション

銀行・郵便局などが提供する郵便番号マスタCSVを**定期的に取得**しているケースで、

- 「今回のファイルで**新たに追加された**郵便番号はどれか？」
- 「前回のファイルにあって**今回廃止された**郵便番号はどれか？」
- 「発行日が明記されていないが、**いつ頃から存在するか**を推定したい」

といった差分管理に使用する。

---

## ロジック詳細

### `compare_postcode.py`

```
旧CSV (FILE_A)  →  postcodesのset_A
新CSV (FILE_B)  →  postcodesのset_B

出力:
  only_in_A  = set_A - set_B   # 旧にあって新にない（廃止候補）
  only_in_B  = set_B - set_A   # 新にあって旧にない（新規追加）
  in_both    = set_A & set_B   # 両方に存在（継続）
```

- `postcode` 列をキーとして読み込み、重複は自動排除（set）
- 出力は `output/` ディレクトリに3ファイル生成

### `enrich_postcode_issue_info.py`

```
旧CSV → postcodesのset（旧）

新CSV の全行をループ:
  if postcode in 旧set:
      issue_info = "already_exists_in_old_file"
      issue_date_estimate = "<=2026-03-05"   # 旧ファイル取得日以前
  else:
      issue_info = "new_in_current_file"
      issue_date_estimate = "2026-03-05"     # 新ファイル取得日で初観測

→ 3列追加した新CSVを output/ に出力
```

- 公式な発行日は元データに存在しないため、あくまで**観測上の推定値**として付与
- 元の全列はそのまま保持し、末尾に `issue_info` / `issue_date_estimate` / `issue_note` を追加

---

## ファイル構成

```
diff_csv/
├── compare_postcode.py             # 差分比較スクリプト
├── enrich_postcode_issue_info.py   # 発行情報付与スクリプト
├── 0305_1518_yubin.csv             # 旧ファイル（入力）
├── 0305_1518_yubin_new.csv         # 新ファイル（入力）
└── output/
    ├── postcode_only_in_0305_1518_yubin.csv      # 旧のみ（廃止候補）
    ├── postcode_only_in_0305_1518_yubin_new.csv  # 新のみ（新規追加）
    ├── postcode_in_both.csv                      # 共通
    └── 0305_1518_yubin_new_with_issue_info.csv   # エンリッチ済み新ファイル
```

---

## 実行方法

```bash
# 差分比較（3ファイル出力）
python compare_postcode.py

# 発行情報付与（エンリッチ済みCSV出力）
python enrich_postcode_issue_info.py
```

### 前提条件

- Python 3.9 以上（標準ライブラリのみ使用、追加インストール不要）
- 入力CSVは UTF-8、1行目がヘッダー行、`postcode` 列が必須

---

## 入力CSVの形式

```csv
postcode,other_col,...
1000001,東京都千代田区千代田,...
```

`postcode` 列さえあれば他の列は自由。`enrich_postcode_issue_info.py` は他の列もそのまま出力に引き継ぐ。
