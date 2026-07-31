# 郵便番号 CSV 差分チェックツール

2つの郵便番号CSVファイルを比較し、追加・廃止・共通の郵便番号を特定するツール群。

---

## できること

1回の実行で以下の4ファイルを `output/` に生成する。

| 出力ファイル | 内容 |
|---|---|
| `postcode_only_in_<旧ファイル名>.csv` | 旧にあって新にない（廃止候補） |
| `postcode_only_in_<新ファイル名>.csv` | 新にあって旧にない（新規追加） |
| `postcode_in_both.csv` | 両方に存在（継続） |
| `<新ファイル名>_with_issue_info.csv` | 新ファイルに発行推定情報を付与したもの |

---

## 想定シチュエーション

銀行・郵便局などが提供する郵便番号マスタCSVを**定期的に取得**しているケースで、

- 「今回のファイルで**新たに追加された**郵便番号はどれか？」
- 「前回のファイルにあって**今回廃止された**郵便番号はどれか？」
- 「発行日が明記されていないが、**いつ頃から存在するか**を推定したい」

といった差分管理に使用する。

---

## ファイル構成

```
diff_csv/
├── run.py              ← ここをダブルクリック or python run.py で実行
├── README.md
├── input/              ← 入力CSVをここに配置
│   ├── 0305_1518_yubin.csv
│   └── 0305_1518_yubin_new.csv
├── output/             ← 実行後に結果が生成される
└── src/
    ├── postcode_diff.py  ← メイン処理（差分比較・エンリッチ）
    └── utils.py          ← 共通関数（load_postcodes）
```

---

## 実行方法

```bash
python run.py
```

または `run.py` をダブルクリック（Python関連付け済みの場合）。

### 前提条件

- Python 3.9 以上（標準ライブラリのみ使用、追加インストール不要）
- 入力CSVは UTF-8、1行目がヘッダー行、`postcode` 列が必須

---

## ロジック詳細

### 差分比較（postcode_diff.py）

```
旧CSV → set_old
新CSV → set_new

only_in_old = set_old - set_new   # 廃止候補
only_in_new = set_new - set_old   # 新規追加
in_both     = set_old & set_new   # 継続
```

### 発行情報付与（postcode_diff.py）

```
新CSVの各行に対して：
  if postcode in set_old:
      issue_info = "already_exists_in_old_file"
      issue_date_estimate = "<=取得日"
  else:
      issue_info = "new_in_current_file"
      issue_date_estimate = "取得日"
```

公式な発行日は元データに存在しないため、あくまで**観測上の推定値**として付与する。

---

## 入力CSVの形式

```csv
postcode,other_col,...
1000001,東京都千代田区千代田,...
```

`postcode` 列さえあれば他の列は自由。エンリッチ出力は他の列もそのまま引き継ぐ。
